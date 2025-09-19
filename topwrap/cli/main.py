# Copyright (c) 2021-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import asyncio
import concurrent.futures
import json
import logging
import subprocess
import sys
import threading
import webbrowser
from itertools import chain
from pathlib import Path
from typing import Any, Optional, Tuple

import click

from topwrap.backend.kpm.backend import KpmDataflowBackend, KpmSpecificationBackend
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.cli import RepositoryPathParam, load_modules_from_repos
from topwrap.cli.repo import repo
from topwrap.config import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_DIR,
    DEFAULT_SERVER_ADDR,
    DEFAULT_SERVER_PORT,
    DEFAULT_WORKSPACE_DIR,
    config,
)
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.fuse_helper import FuseSocBuilder
from topwrap.kpm_common import RPCparams
from topwrap.kpm_topwrap_client import kpm_run_client
from topwrap.resource_field import FileReferenceHandler

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


@click.group(help="Topwrap")
@click.option(
    "--log-level",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
    default="INFO",
    show_default=True,
    help="Log level",
)
@click.option(
    "--repo",
    multiple=True,
    type=RepositoryPathParam(path_type=Path),
    help="Additional user repository to load",
)
def main(log_level: str, repo: tuple[Path]):
    logging.basicConfig(level=log_level)
    logging.getLogger().setLevel(log_level)
    for rep in repo:
        config.repositories[rep.name] = FileReferenceHandler(rep)


main.add_command(repo)


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
def build_main(
    sources: Tuple[Path, ...],
    design: Path,
    build_dir: Path,
    fuse: bool,
    part: Optional[str],
    iface_compliance: bool,
):
    config.force_interface_compliance = iface_compliance

    all_sources = list(sources)

    [*repo_modules] = load_modules_from_repos()

    frontend = YamlFrontend(repo_modules)
    [module] = frontend.parse_files([design])

    backend = SystemVerilogBackend()
    repr = backend.represent(module)
    [out] = backend.serialize(repr, combine=True)

    build_dir.mkdir(exist_ok=True)
    out.save(build_dir)

    if fuse:
        if part is None:
            logging.warning(
                "You didn't specify the part number using the --part option. "
                "It will remain unspecified in the generated FuseSoC .core "
                "and your further implementation/synthesis may fail."
            )

        fuse_builder = FuseSocBuilder(part)

        fuse_builder.add_source(out.filename, "systemVerilogSource")
        fuse_builder.build(
            module.id.name, build_dir / f"{module.id.name}.core", sources_dir=all_sources
        )


class KPM:
    @staticmethod
    def build_server(**params_dict: Any):
        args = ["pipeline_manager", "build", "server-app"]
        for k, v in params_dict.items():
            Path(v).mkdir(exist_ok=True, parents=True)
            args += [f"--{k}".replace("_", "-"), f"{v}"]
        subprocess.check_call([sys.executable, "-m", *args])

    @staticmethod
    def run_server(
        server_ready_event: Optional[threading.Event] = None,
        server_init_failed: Optional[threading.Event] = None,
        show_kpm_logs: bool = True,
        shutdown_server: bool = False,
        **params_dict: Any,
    ):
        args = ["pipeline_manager", "run"]
        for k, v in params_dict.items():
            args += [f"--{k}".replace("_", "-"), f"{v}"]

        server_process = subprocess.Popen(
            [sys.executable, "-m", *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        server_ready_string = "Uvicorn running on"
        while server_process.poll() is None and server_process.stdout is not None:
            server_logs = server_process.stdout.readline().decode("utf-8")
            if server_ready_event is not None and server_ready_string in server_logs:
                server_ready_event.set()
                if shutdown_server:
                    server_process.terminate()
            if show_kpm_logs:
                sys.stdout.write(server_logs)
        else:
            logging.warning("KPM server has been terminated")
            if server_ready_event is not None and not server_ready_event.is_set():
                if server_init_failed is not None:
                    server_init_failed.set()
                # Remove the server ready event block
                server_ready_event.set()
                logging.warning(
                    "Make sure that there isn't any instance of pipeline manager running in the"
                    " background"
                )

    @staticmethod
    def run_client(
        host: str,
        port: int,
        design: Optional[Path],
        yamlfiles: Tuple[Path, ...],
        build_dir: Path,
        client_ready_event: Optional[threading.Event] = None,
    ):
        logging.info("Starting kenning pipeline manager client")

        [*repo_mods] = load_modules_from_repos()

        frontend = YamlFrontend(repo_mods)
        design_module = next(frontend.parse_files([design])) if design else None
        if design_module and not design_module.design:
            logging.error("Given design YAML file does not contain a design.")
            return

        modules = frontend.parse_files(yamlfiles)

        spec = KpmSpecificationBackend.default()

        for module in chain(repo_mods, modules):
            try:
                spec.add_module(module)
            except Exception:
                logging.error(
                    "An error occurred while generating specification for module "
                    f"'{module.id.name}' from '{module.refs[0].file}'"
                )
                return

        if design_module:
            try:
                spec.add_module(design_module, recursive=True)
            except Exception:
                logging.error(
                    "An error occurred while generating specification for design module "
                    f"'{design_module.id.name}' from '{design_module.refs[0].file}'"
                )
                return

        spec = spec.build()

        asyncio.run(
            kpm_run_client(
                RPCparams(
                    host, port, spec, build_dir, design_module.design if design_module else None
                ),
                client_ready_event,
            )
        )


@main.command("kpm_client", help="Run a client app, that connects to a running KPM server")
@click.option("--host", "-h", default=DEFAULT_SERVER_ADDR, help="KPM server address")
@click.option("--port", "-p", default=DEFAULT_SERVER_PORT, help="KPM server listening port")
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
    design: Optional[Path],
    yamlfiles: Tuple[Path, ...],
    build_dir: Path,
):
    KPM.run_client(host, port, design, yamlfiles, build_dir)


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
@click.argument("yamlfiles", type=click_r_file, nargs=-1)
def topwrap_gui(
    design: Optional[Path],
    yamlfiles: Tuple[Path, ...],
    frontend_directory: Path,
    workspace_directory: Path,
    server_host: str,
    server_port: int,
    backend_host: str,
    backend_port: int,
    use_server: bool = True,
):
    logging.info("Checking if server is built")
    if (not frontend_directory.exists() or not workspace_directory.exists()) and use_server:
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

        if use_server:
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
            if server_init_failed.is_set():
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
            build_dir=Path("build"),
            client_ready_event=client_ready_event,
        )
        client_ready_event.wait()

        if use_server:
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
    [*repo_mods] = load_modules_from_repos()
    frontend = YamlFrontend(repo_mods)
    design_module = next(frontend.parse_files([design])) if design else None
    modules = frontend.parse_files(list(files))

    spec = KpmSpecificationBackend.default()
    for module in modules:
        try:
            spec.add_module(module)
        except Exception:
            logging.error(
                "An error occurred while generating specification for module "
                f"'{module.id.name}' from '{module.refs[0].file}'"
            )
            sys.exit(1)

    try:
        if design_module:
            spec.add_module(design_module, recursive=True)
    except Exception:
        assert design_module
        logging.error(
            "An error occurred while generating specification for design module "
            f"'{design_module.id.name}' from '{design_module.refs[0].file}'"
        )
        sys.exit(1)
    spec = spec.build()

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
    [*repo_mods] = load_modules_from_repos()
    frontend = YamlFrontend(repo_mods)
    design_module = next(frontend.parse_files([design]))
    if not design_module.design:
        logging.error("Given design YAML file does not contain a design.")
        sys.exit(1)

    modules = frontend.parse_files(list(files))

    spec = KpmSpecificationBackend.default()
    for module in modules:
        try:
            spec.add_module(module)
        except Exception:
            logging.error(
                "An error occurred while generating specification for module "
                f"'{module.id.name}' from '{module.refs[0].file}'"
            )
            sys.exit(1)

    try:
        spec.add_module(design_module, recursive=True)
    except Exception:
        logging.error(
            "An error occurred while generating specification for design module "
            f"'{design_module.id.name}' from '{design_module.refs[0].file}'"
        )
        sys.exit(1)
    spec = spec.build()

    dataflow = KpmDataflowBackend(spec)
    try:
        dataflow.represent_design(design_module.design, depth=-1)
    except Exception:
        logging.error(
            "An error occurred while generating dataflow for design "
            f"'{design_module.id.name} from '{design_module.refs[0].file}'"
        )
        sys.exit(1)
    dataflow = dataflow.build()

    with open(output, "w") as f:
        f.write(json.dumps(dataflow))
