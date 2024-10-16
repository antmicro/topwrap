# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import click

from topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from topwrap.kpm_common import RPCparams
from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

from .config import config
from .design import DesignDescription, build_design_from_yaml
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
@click.option("--part", "-p", help="FPGA part name")
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
    part: Optional[str],
    iface_compliance: bool,
    log_level: str,
):
    configure_log_level(log_level)
    config.force_interface_compliance = iface_compliance

    if part is None:
        logging.warning(
            "You didn't specify part number. 'None' will be used "
            "and thus your implementation may fail."
        )

    config_user_repo = UserRepo()
    config_user_repo.load_repositories_from_paths(config.get_repositories_paths())
    all_sources = config_user_repo.get_srcs_dirs_for_cores()
    all_sources.extend(sources)

    # following function does make sure that build directory exists
    # so we don't explicitly create build directory here
    build_design_from_yaml(design, build_dir, all_sources, part)


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
            "hdlConvertor not installed, please install optional dependency topwrap-parse "
            "e.g. pip install topwrap[topwrap-parse]"
        )

    configure_log_level(log_level)
    dest_dir.mkdir(exist_ok=True, parents=True)

    for filepath in files:
        if filepath.suffix == ".v":
            modules = VerilogModuleGenerator().get_modules(filepath)
            iface_grouper = standard_iface_grouper(filepath, use_yosys, iface_deduce, iface)
            for verilog_mod in modules:
                ipcore_desc = verilog_mod.to_ip_core_description(iface_grouper)
                yaml_path = dest_dir / f"gen_{ipcore_desc.name}.yaml"
                ipcore_desc.save(yaml_path)
                logging.info(
                    f"Verilog module '{verilog_mod.module_name}'" f"saved in file '{yaml_path}'"
                )
        elif filepath.suffix in (".vhdl", ".vhd"):
            # TODO - handle case with multiple VHDL modules in one file
            vhdl_mod = VHDLModule(filepath)
            iface_grouper = standard_iface_grouper(filepath, False, iface_deduce, iface)
            ipcore_desc = vhdl_mod.to_ip_core_description(iface_grouper)
            yaml_path = dest_dir / f"gen_{ipcore_desc.name}.yaml"
            ipcore_desc.save(yaml_path)
            logging.info(f"VHDL Module '{vhdl_mod.module_name}'" f"saved in file '{yaml_path}'")


DEFAULT_WORKSPACE_DIR = Path("build", "workspace")
DEFAULT_BACKEND_DIR = Path("build", "backend")
DEFAULT_FRONTEND_DIR = Path("build", "frontend")
DEFAULT_SERVER_ADDR = "127.0.0.1"
DEFAULT_SERVER_PORT = 9000
DEFAULT_BACKEND_ADDR = "127.0.0.1"
DEFAULT_BACKEND_PORT = 5000


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
    configure_log_level(log_level)

    logging.info("Starting kenning pipeline manager client")
    config_user_repo = UserRepo()
    config_user_repo.load_repositories_from_paths(config.get_repositories_paths())
    extended_yamlfiles = config_user_repo.get_core_designs()
    extended_yamlfiles += yamlfiles

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        kpm_run_client(RPCparams(host, port, extended_yamlfiles, build_dir, design))
    )


@main.command("kpm_build_server", help="Build KPM server")
@click.option(
    "--workspace-directory",
    type=click_opt_rw_dir,
    default=DEFAULT_WORKSPACE_DIR,
    help="Directory where the frontend sources should be stored",
)
@click.option(
    "--output-directory",
    type=click_opt_rw_dir,
    default=DEFAULT_FRONTEND_DIR,
    help="Directory where the built frontend should be stored",
)
@click.pass_context
def kpm_build_server(ctx: click.Context, workspace_directory: Path, output_directory: Path):
    workspace_directory.mkdir(exist_ok=True, parents=True)
    output_directory.mkdir(exist_ok=True, parents=True)
    args = ["pipeline_manager", "build", "server-app"]
    for k, v in ctx.params.items():
        args += [f"--{k}".replace("_", "-"), f"{v}"]
    subprocess.check_call(args)


@main.command("kpm_run_server", help="Run a KPM server")
@click.option(
    "--frontend-directory",
    type=click_r_dir,
    default=DEFAULT_FRONTEND_DIR,
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
@click.pass_context
def kpm_run_server(ctx: click.Context, **_):
    args = ["pipeline_manager", "run"]
    for k, v in ctx.params.items():
        args += [f"--{k}".replace("_", "-"), f"{v}"]
    subprocess.check_call(args)


@main.command("specification", help="Generate KPM specification from IP core YAMLs")
@click.option(
    "--output",
    "-o",
    type=click_w_file,
    default="kpm_spec.json",
    help="Destination file for the KPM specification",
)
@click.argument("files", type=click_r_file, nargs=-1)
def generate_kpm_spec(output: Path, files: Tuple[Path, ...]):
    config_user_repo = UserRepo()
    config_user_repo.load_repositories_from_paths(config.get_repositories_paths())
    extended_yamlfiles = config_user_repo.get_core_designs()
    extended_yamlfiles += files

    spec = ipcore_yamls_to_kpm_spec(extended_yamlfiles)
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
    config_user_repo = UserRepo()
    config_user_repo.load_repositories_from_paths(config.get_repositories_paths())
    extended_yamlfiles = config_user_repo.get_core_designs()
    extended_yamlfiles += files

    spec = ipcore_yamls_to_kpm_spec(extended_yamlfiles)
    dataflow = kpm_dataflow_from_design_descr(DesignDescription.load(design), spec)
    with open(output, "w") as f:
        f.write(json.dumps(dataflow))
