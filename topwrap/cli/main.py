# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import queue
import subprocess
import sys
import threading
import webbrowser
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional, Tuple

import rich.console
from cyclopts.types import ExistingDirectory, ExistingFile

from topwrap.backend.kpm.backend import KpmDataflowBackend, KpmSpecificationBackend
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.cli import (
    cli,
    load_interfaces_from_repos,
    load_modules_from_repos,
)
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

logger = logging.getLogger(__name__)


def main():
    cli.meta(console=rich.console.Console(no_color=True))


@cli.command(name="build")
def build_main(
    *,
    sources: Tuple[ExistingDirectory, ...] = (),
    design: ExistingFile,
    build_dir: Optional[Path] = None,
    fuse: bool = False,
    part: Optional[str] = None,
    iface_compliance: bool = False,
):
    """Generate SystemVerilog from a top design YAML file.

    Parameters
    ----------
    sources
        Directories to scan for additional sources.
    design
        Top design file.
    build_dir
        Output directory for generated files.
    fuse
        Generate a FuseSoC .core file for further synthesis.
    part
        FPGA part number (ignored without --fuse).
    iface_compliance
        Force interface compliance checking.
    """
    if build_dir is None:
        build_dir = Path("build")

    config.force_interface_compliance = iface_compliance

    all_sources = list(sources)

    repo_modules, existing_ifaces = load_modules_from_repos()

    frontend = YamlFrontend(repo_modules)
    frontend_output = frontend.parse_files([design])
    module = frontend_output.modules[0]

    backend = SystemVerilogBackend(existing_ifaces)
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
    child_processes = []
    kpm_run_client_task: Optional[asyncio.Task[Any]] = None

    @staticmethod
    def cleanup():
        for child in KPM.child_processes:
            child.terminate()
        if KPM.kpm_run_client_task:
            KPM.kpm_run_client_task.cancel()

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
        KPM.child_processes.append(server_process)
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
                logging.warning(
                    "Make sure that there isn't any instance of pipeline manager running in the"
                    " background"
                )
                raise Exception("Failed to initialize KPM server")

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

        repo_modules, _ = load_modules_from_repos()

        frontend = YamlFrontend(repo_modules)
        if design is not None:
            design_module = frontend.parse_design_file(design).modules[0]
        else:
            design_module = None
        if design_module and not design_module.design:
            logging.error("Given design YAML file does not contain a design.")
            return

        modules = frontend.parse_module_files(list(yamlfiles)).modules

        spec = KpmSpecificationBackend.default()

        for module in chain(repo_modules, modules):
            try:
                spec.add_module(module)
            except Exception:
                logging.error(
                    "An error occurred while generating specification for module "
                    f"'{module.id.name}' from '{module.refs[0].file}'"
                )
                return

        if design_module:
            assert design_module.design
            design_module.design.update_interconnects_from_memory_maps()
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
            KPM._run_client(
                kpm_run_client(
                    RPCparams(
                        host,
                        port,
                        spec,
                        build_dir,
                        design_module.design if design_module else None,
                        list(repo_modules) + modules,
                        [*load_interfaces_from_repos()],
                    ),
                    client_ready_event,
                )
            )
        )

    @staticmethod
    async def _run_client(coro: Coroutine[None, None, None]):
        KPM.kpm_run_client_task = asyncio.create_task(coro)
        await KPM.kpm_run_client_task


@cli.command(name="kpm_client")
def kpm_client_main(
    yamlfiles: Tuple[ExistingFile, ...] = (),
    *,
    host: str = DEFAULT_SERVER_ADDR,
    port: int = DEFAULT_SERVER_PORT,
    design: Optional[ExistingFile] = None,
    build_dir: Optional[Path] = None,
):
    """Run a client app that connects to a running KPM server.

    Parameters
    ----------
    yamlfiles
        Module YAML files to load.
    host
        KPM server address.
    port
        KPM server listening port.
    design
        Design file to load initially.
    build_dir
        Output directory for generated files.
    """
    if build_dir is None:
        build_dir = Path("build")

    KPM.run_client(host, port, design, yamlfiles, build_dir)
    KPM.cleanup()


@cli.command(name="kpm_build_server")
def kpm_build_server(
    workspace_directory: Optional[Path] = None,
    output_directory: Optional[Path] = None,
):
    """Build KPM server"""
    if workspace_directory is None:
        workspace_directory = Path(config.kpm_build_location) / DEFAULT_WORKSPACE_DIR

    if output_directory is None:
        output_directory = Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR

    KPM.build_server(
        workspace_directory=workspace_directory,
        output_directory=output_directory,
    )


@cli.command(name="kpm_run_server")
def kpm_run_server(
    frontend_directory: Optional[ExistingDirectory] = None,
    server_host: str = DEFAULT_SERVER_ADDR,
    server_port: int = DEFAULT_SERVER_PORT,
    backend_host: str = DEFAULT_BACKEND_ADDR,
    backend_port: int = DEFAULT_BACKEND_PORT,
    verbosity: str = "INFO",
):
    """Run a KPM server"""
    if frontend_directory is None:
        frontend_directory = Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR

    try:
        KPM.run_server(
            frontend_directory=frontend_directory,
            server_host=server_host,
            server_port=server_port,
            backend_host=backend_host,
            backend_port=backend_port,
            verbosity=verbosity,
        )
    except Exception as e:
        logging.error(f"{e}")
    KPM.cleanup()


@cli.command(name="gui")
def topwrap_gui(
    yamlfiles: Tuple[ExistingFile, ...] = (),
    *,
    design: Optional[ExistingFile] = None,
    frontend_directory: Optional[Path] = None,
    workspace_directory: Optional[Path] = None,
    server_host: str = DEFAULT_SERVER_ADDR,
    server_port: int = DEFAULT_SERVER_PORT,
    backend_host: str = DEFAULT_BACKEND_ADDR,
    backend_port: int = DEFAULT_BACKEND_PORT,
    use_server: bool = True,
    raise_exception: bool = False,
):
    """Start GUI

    Parameters
    ----------
    design
        Design file to load initially.
    server_host
        Host of the Pipeline Manager TCP server.
    server_port
        Port of the Pipeline Manager TCP server.
    """
    if frontend_directory is None:
        frontend_directory = Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR

    if workspace_directory is None:
        workspace_directory = Path(config.kpm_build_location) / DEFAULT_WORKSPACE_DIR

    logging.info("Checking if server is built")
    if (not frontend_directory.exists() or not workspace_directory.exists()) and use_server:
        logging.info("Server build is incomplete, building now")
        KPM.build_server(
            workspace_directory=workspace_directory, output_directory=frontend_directory
        )
    else:
        logging.info("Server build found")

    logging.info("Starting server")
    server_ready_event = threading.Event()
    error_queue = queue.Queue()

    threading.excepthook = lambda args, error_queue=error_queue: error_queue.put(args)

    def wait_for_event_or_raise_error(
        event: Callable[[], bool], error_queue: queue.Queue[threading.ExceptHookArgs]
    ):
        while True:
            if not event():
                break
            try:
                except_hook_args = error_queue.get(timeout=0.5)
                raise except_hook_args.exc_value
            except queue.Empty:
                pass

    try:
        server_thread = threading.Thread(
            target=KPM.run_server,
            daemon=True,
            kwargs={
                "server_ready_event": server_ready_event,
                "show_kpm_logs": False,
                "server_host": server_host,
                "server_port": server_port,
                "backend_host": backend_host,
                "backend_port": backend_port,
                "frontend_directory": frontend_directory,
            },
        )
        if use_server:
            server_thread.start()

            logging.info("Waiting for KPM server to initialize")

            while True:
                if server_ready_event.is_set():
                    break
                try:
                    except_hook_args = error_queue.get(timeout=0.5)
                    raise except_hook_args.exc_value
                except queue.Empty:
                    pass

            logging.info("KPM server initialized")

        client_ready_event = threading.Event()
        client_thread = threading.Thread(
            target=KPM.run_client,
            daemon=True,
            kwargs={
                "design": design,
                "yamlfiles": yamlfiles,
                "host": server_host,
                "port": server_port,
                "build_dir": Path("build"),
                "client_ready_event": client_ready_event,
            },
        )
        client_thread.start()

        wait_for_event_or_raise_error(client_ready_event.is_set, error_queue)

        if use_server:
            logging.info("Opening browser with KPM GUI")
            webbrowser.open(f"http://{backend_host}:{backend_port}")

        wait_for_event_or_raise_error(server_thread.is_alive, error_queue)

    except Exception as e:
        logging.error(f"{e}")
        if raise_exception:
            raise e
    KPM.cleanup()


@cli.command(name="specification")
def generate_kpm_spec(
    files: Tuple[ExistingFile, ...] = (),
    *,
    design: Optional[ExistingFile] = None,
    output: Optional[Path] = None,
):
    """Generate KPM specification from IP core YAMLs"""

    if output is None:
        output = Path("kpm_spec.json")

    repo_modules, _ = load_modules_from_repos()

    frontend = YamlFrontend(repo_modules)
    design_module = None
    if design is not None:
        design_module = frontend.parse_design_file(design).modules[0]
    modules = frontend.parse_module_files(list(files)).modules

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
    if design_module and design_module.design:
        design_module.design.update_interconnects_from_memory_maps()
        flow = KpmDataflowBackend(spec)
        flow.represent_design(design_module.design, depth=-1)
        spec = flow.apply_subgraphs_to_spec(spec)

    with open(output, "w") as f:
        f.write(json.dumps(spec))


@cli.command(name="dataflow")
def generate_kpm_design(
    files: Tuple[ExistingFile, ...] = (),
    *,
    design: ExistingFile,
    output: Optional[Path] = None,
):
    """Generate KPM dataflow from IP core YAMLs and a design YAML"""

    if output is None:
        output = Path("kpm_dataflow.json")

    repo_modules, _ = load_modules_from_repos()

    frontend = YamlFrontend(repo_modules)
    design_module = frontend.parse_design_file(design).modules[0]

    if not design_module.design:
        logging.error("Given design YAML file does not contain a design.")
        sys.exit(1)

    design_module.design.update_interconnects_from_memory_maps()

    modules = frontend.parse_module_files(list(files)).modules

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
