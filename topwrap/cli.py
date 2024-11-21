# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import asyncio
import concurrent.futures
import json
import logging
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any, Optional, Tuple

import click

from topwrap.config import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_DIR,
    DEFAULT_SERVER_ADDR,
    DEFAULT_SERVER_PORT,
    DEFAULT_WORKSPACE_DIR,
)
from topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from topwrap.kpm_common import RPCparams
from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

from .config import config
from .design import DesignDescription
from .interface_grouper import standard_iface_grouper
from .kpm_topwrap_client import kpm_run_client
from .repo.user_repo import UserRepo

click_r_dir = click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path)
click_opt_rw_dir = click.Path(
    exists=False, file_okay=False, dir_okay=True, readable=True, writable=True, path_type=Path
)
click_r_file = click.Path(
    exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
)
click_w_file = click.Path(
    exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path
)

main = click.Group(help="Topwrap")

AVAILABLE_LOG_LEVELS = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "WARNING"


def configure_log_level(log_level: str):
    logging.basicConfig(level=DEFAULT_LOG_LEVEL)
    if log_level not in AVAILABLE_LOG_LEVELS:
        logging.warning(f"Wrong log-level value: {log_level}. Select one of {AVAILABLE_LOG_LEVELS}")

    logger = logging.getLogger()
    logger.setLevel(log_level)


def load_user_repos() -> UserRepo:
    repo = UserRepo()
    repo.load_repositories_from_paths(config.get_repositories_paths())
    return repo


@main.command("build", help="Generate top module")
@click.option(
    "--sources",
    "-s",
    type=click_r_dir,
    multiple=True,
    help="Specify directory to scan for additional sources",
)
@click.option("--design", "-d", type=click_r_file, required=True, help="Specify top design file")
@click.option(
    "--build-dir",
    "-b",
    type=click_opt_rw_dir,
    default="build",
    help="Specify directory name for output files",
)
@click.option(
    "--fuse",
    "-f",
    default=False,
    is_flag=True,
    help="Generate a FuseSoC .core file for further synthesis",
)
@click.option("--part", "-p", help="Specify the FPGA part number (ignored without --fuse)")
@click.option(
    "--iface-compliance/--no-iface-compliance",
    default=False,
    help="Force compliance checks for predefined interfaces",
)
@click.option("--log-level", default=DEFAULT_LOG_LEVEL, help="Log level")
def build_main(
    sources: Tuple[Path, ...],
    design: Path,
    build_dir: Path,
    fuse: bool,
    part: Optional[str],
    iface_compliance: bool,
    log_level: str,
):
    configure_log_level(log_level)
    config.force_interface_compliance = iface_compliance

    config_user_repo = load_user_repos()
    all_sources = config_user_repo.get_srcs_dirs_for_cores()
    all_sources.extend(sources)

    desc = DesignDescription.load(design)
    name = desc.design.name or "top"
    ipc = desc.to_ip_connect(design.parent)
    ipc.generate_top(name, build_dir)

    if fuse:
        if part is None:
            logging.warning(
                "You didn't specify the part number using the --part option. "
                "It will remain unspecified in the generated FuseSoC .core "
                "and your further implementation/synthesis may fail."
            )
        ipc.generate_fuse_core(name, build_dir, sources, part)


@main.command("parse", help="Parse HDL sources to ip core yamls")
@click.option(
    "--use-yosys",
    default=False,
    is_flag=True,
    help="Use Yosys command `read_verilog` to parse Verilog files",
)
@click.option(
    "--iface-deduce",
    default=False,
    is_flag=True,
    help="Try to group port into interfaces automatically",
)
@click.option(
    "--iface", "-i", multiple=True, help="Interface name, that ports will be grouped into"
)
@click.option(
    "--dest-dir",
    "-d",
    type=click_opt_rw_dir,
    default="./",
    help="Destination directory for generated yamls",
)
@click.option("--log-level", default=DEFAULT_LOG_LEVEL, help="Log level")
@click.argument("files", type=click_r_file, nargs=-1)
def parse_main(
    use_yosys: bool,
    iface_deduce: bool,
    iface: Tuple[str, ...],
    dest_dir: Path,
    log_level: str,
    files: Tuple[Path, ...],
):
    try:
        from .verilog_parser import VerilogModuleGenerator
        from .vhdl_parser import VHDLModule
    except ModuleNotFoundError:
        raise RuntimeError(
            "hdlConvertor not installed, please install optional dependency topwrap[parse]"
            "e.g. pip install topwrap[parse]"
        )

    configure_log_level(log_level)
    dest_dir.mkdir(exist_ok=True, parents=True)

    for filepath in files:
        if filepath.suffix == ".v":
            modules = VerilogModuleGenerator().get_modules(filepath)
            iface_grouper = standard_iface_grouper(filepath, use_yosys, iface_deduce, iface)
            for verilog_mod in modules:
                ipcore_desc = verilog_mod.to_ip_core_description(iface_grouper)
                yaml_path = dest_dir / f"{ipcore_desc.name}.yaml"
                ipcore_desc.save(yaml_path)
                logging.info(
                    f"Verilog module '{verilog_mod.module_name}'" f"saved in file '{yaml_path}'"
                )
        elif filepath.suffix in (".vhdl", ".vhd"):
            # TODO - handle case with multiple VHDL modules in one file
            vhdl_mod = VHDLModule(filepath)
            iface_grouper = standard_iface_grouper(filepath, False, iface_deduce, iface)
            ipcore_desc = vhdl_mod.to_ip_core_description(iface_grouper)
            yaml_path = dest_dir / f"{ipcore_desc.name}.yaml"
            ipcore_desc.save(yaml_path)
            logging.info(f"VHDL Module '{vhdl_mod.module_name}'" f"saved in file '{yaml_path}'")


class KPM:
    @staticmethod
    def build_server(**params_dict: Any):
        args = ["pipeline_manager", "build", "server-app"]
        for k, v in params_dict.items():
            Path(v).mkdir(exist_ok=True, parents=True)
            args += [f"--{k}".replace("_", "-"), f"{v}"]
        subprocess.check_call(args)

    @staticmethod
    def run_server(
        server_ready_event: Optional[threading.Event] = None,
        server_init_failed: Optional[threading.Event] = None,
        show_kpm_logs: bool = True,
        **params_dict: Any,
    ):
        args = ["pipeline_manager", "run"]
        for k, v in params_dict.items():
            args += [f"--{k}".replace("_", "-"), f"{v}"]

        server_process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        server_ready_string = "Uvicorn running on"
        while server_process.poll() is None and server_process.stdout is not None:
            server_logs = server_process.stdout.readline().decode("utf-8")
            if server_ready_event is not None and server_ready_string in server_logs:
                server_ready_event.set()
            if show_kpm_logs:
                sys.stdout.write(server_logs)
        else:
            logging.warning("KPM server has been terminated")
            if server_ready_event is not None and not server_ready_event.isSet():
                if server_init_failed is not None:
                    server_init_failed.set()
                # Remove the server ready event block
                server_ready_event.set()
                logging.warning(
                    "Make sure that there isn't any instance of pipeline manager running in the background"
                )

    @staticmethod
    def run_client(
        host: str,
        port: int,
        log_level: str,
        design: Optional[Path],
        yamlfiles: Tuple[Path, ...],
        build_dir: Path,
        client_ready_event: Optional[threading.Event] = None,
    ):
        configure_log_level(log_level)
        logging.info("Starting kenning pipeline manager client")
        config_user_repo = load_user_repos()
        design_desc = DesignDescription.load(design) if design else None
        spec = ipcore_yamls_to_kpm_spec(
            config_user_repo.get_core_designs() + list(yamlfiles), design_desc
        )
        asyncio.run(
            kpm_run_client(RPCparams(host, port, spec, build_dir, design_desc), client_ready_event)
        )


@main.command("kpm_client", help="Run a client app, that connects to a running KPM server")
@click.option("--host", "-h", default=DEFAULT_SERVER_ADDR, help="KPM server address")
@click.option("--port", "-p", default=DEFAULT_SERVER_PORT, help="KPM server listening port")
@click.option("--log-level", default=DEFAULT_LOG_LEVEL, help="Log level")
@click.option(
    "--design",
    "-d",
    type=click_r_file,
    help="Specify design file to load initially",
)
@click.option(
    "--build-dir",
    "-b",
    type=click_opt_rw_dir,
    default="build",
    help="Specify directory name for output files",
)
@click.argument("yamlfiles", type=click_r_file, nargs=-1)
def kpm_client_main(
    host: str,
    port: int,
    log_level: str,
    design: Optional[Path],
    yamlfiles: Tuple[Path, ...],
    build_dir: Path,
):
    KPM.run_client(host, port, log_level, design, yamlfiles, build_dir)


@main.command("kpm_build_server", help="Build KPM server")
@click.option(
    "--workspace-directory",
    type=click_opt_rw_dir,
    default=Path(config.kpm_build_location) / DEFAULT_WORKSPACE_DIR,
    help="Directory where the frontend sources should be stored",
)
@click.option(
    "--output-directory",
    type=click_opt_rw_dir,
    default=Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR,
    help="Directory where the built frontend should be stored",
)
@click.pass_context
def kpm_build_server_ctx(ctx: click.Context, **_):
    KPM.build_server(**ctx.params)


@main.command("kpm_run_server", help="Run a KPM server")
@click.option(
    "--frontend-directory",
    type=click_r_dir,
    default=Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR,
    help="Location of the built frontend",
)
@click.option(
    "--server-host",
    default=DEFAULT_SERVER_ADDR,
    help="The address of the Pipeline Manager TCP Server",
)
@click.option(
    "--server-port", default=DEFAULT_SERVER_PORT, help="The port of the Pipeline Manager TCP Server"
)
@click.option(
    "--backend-host",
    default=DEFAULT_BACKEND_ADDR,
    help="The address of the backend of Pipeline Manager",
)
@click.option(
    "--backend-port",
    default=DEFAULT_BACKEND_PORT,
    help="The port of the backend of Pipeline Manager",
)
@click.option("--verbosity", default="INFO", help="Verbosity level for KPM server logs")
@click.pass_context
def kpm_run_server_ctx(ctx: click.Context, **_):
    KPM.run_server(**ctx.params)


@main.command("gui", help="Start GUI")
@click.option(
    "--server-host",
    default=DEFAULT_SERVER_ADDR,
    help="The address of the Pipeline Manager TCP Server",
)
@click.option(
    "--server-port", default=DEFAULT_SERVER_PORT, help="The port of the Pipeline Manager TCP Server"
)
@click.option(
    "--backend-host",
    default=DEFAULT_BACKEND_ADDR,
    help="The address of the backend of Pipeline Manager",
)
@click.option(
    "--backend-port",
    default=DEFAULT_BACKEND_PORT,
    help="The port of the backend of Pipeline Manager",
)
@click.option(
    "--design",
    "-d",
    type=click_r_file,
    help="Specify design file to load initially",
)
@click.option(
    "--frontend-directory",
    type=click_opt_rw_dir,
    default=Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR,
    help="Location of the built frontend",
)
@click.option(
    "--workspace-directory",
    type=click_opt_rw_dir,
    default=Path(config.kpm_build_location) / DEFAULT_WORKSPACE_DIR,
    help="Directory where the frontend sources should be stored",
)
@click.option("--log-level", default="INFO", help="Log level")
@click.argument("yamlfiles", type=click_r_file, nargs=-1)
def topwrap_gui(
    design: Optional[Path],
    log_level: str,
    yamlfiles: Tuple[Path, ...],
    frontend_directory: Path,
    workspace_directory: Path,
    server_host: str,
    server_port: int,
    backend_host: str,
    backend_port: int,
):
    configure_log_level(log_level)
    logging.info("Checking if server is built")
    if not frontend_directory.exists() or not workspace_directory.exists():
        logging.info("Server build is incomplete, building now")
        KPM.build_server(
            workspace_directory=workspace_directory, output_directory=frontend_directory
        )
    else:
        logging.info("Server build found")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        logging.info("Starting server")
        server_ready_event = threading.Event()
        server_init_failed = threading.Event()

        executor.submit(
            KPM.run_server,
            server_ready_event=server_ready_event,
            show_kpm_logs=False,
            server_init_failed=server_init_failed,
            server_host=server_host,
            server_port=server_port,
            backend_host=backend_host,
            backend_port=backend_port,
            frontend_directory=frontend_directory,
        )
        logging.info("Waiting for KPM server to initialize")
        server_ready_event.wait()
        if server_init_failed.isSet():
            logging.error("KPM server failed to initialize. Aborting")
            return
        logging.info("KPM server initialized")
        client_ready_event = threading.Event()
        executor.submit(
            KPM.run_client,
            design=design,
            yamlfiles=yamlfiles,
            host=server_host,
            port=server_port,
            log_level=log_level,
            build_dir=Path("build"),
            client_ready_event=client_ready_event,
        )
        client_ready_event.wait()
        logging.info("Opening browser with KPM GUI")
        webbrowser.open(f"{backend_host}:{backend_port}")


@main.command("specification", help="Generate KPM specification from IP core YAMLs")
@click.option(
    "--output",
    "-o",
    type=click_w_file,
    default="kpm_spec.json",
    help="Destination file for the KPM specification",
)
@click.option("--design", "-d", type=click_r_file, help="Design YAML file")
@click.argument("files", type=click_r_file, nargs=-1)
def generate_kpm_spec(output: Path, design: Optional[Path], files: Tuple[Path, ...]):
    config_user_repo = load_user_repos()
    yamls = list(files) + config_user_repo.get_core_designs()
    spec = ipcore_yamls_to_kpm_spec(yamls, DesignDescription.load(design) if design else None)
    with open(output, "w") as f:
        f.write(json.dumps(spec))


@main.command("dataflow", help="Generate KPM dataflow from IP core YAMLs and a design YAML")
@click.option(
    "--output",
    "-o",
    type=click_w_file,
    default="kpm_dataflow.json",
    help="Destination file for the KPM dataflow",
)
@click.option("--design", "-d", required=True, type=click_r_file, help="Design YAML file")
@click.argument("files", type=click_r_file, nargs=-1)
def generate_kpm_design(output: Path, design: Path, files: Tuple[Path, ...]):
    config_user_repo = load_user_repos()
    yamls = list(files) + config_user_repo.get_core_designs()
    design_desc = DesignDescription.load(design)
    spec = ipcore_yamls_to_kpm_spec(yamls, design_desc)
    dataflow = kpm_dataflow_from_design_descr(design_desc, spec)
    with open(output, "w") as f:
        f.write(json.dumps(dataflow))
