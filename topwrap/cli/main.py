# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import queue
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional, Tuple, cast

import rich.console
from cyclopts.types import ExistingDirectory, ExistingFile

from topwrap.cli import cli
from topwrap.config import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_DIR,
    DEFAULT_SERVER_ADDR,
    DEFAULT_SERVER_PORT,
    DEFAULT_WORKSPACE_DIR,
    config,
)
from topwrap.kpm_common import RPCparams
from topwrap.kpm_topwrap_client import kpm_run_client
from topwrap.plugin.base import BuildException
from topwrap.plugin.pipeline import BuildPipeline
from topwrap.plugin.steps import KpmSpecificationOutputStage
from topwrap.util import JsonType

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

    try:
        pipeline = BuildPipeline.yaml_sv_pipeline(
            fuse=fuse, fuse_part=part, fuse_src_dirs=list(sources)
        )
        pipeline.run_files([], design, build_dir)
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)


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

        try:
            pipeline = BuildPipeline.yaml_kpm_spec_pipeline()
            pipeline.prepare_files(list(yamlfiles), design)
            pipeline.process()

            ctx = pipeline.ctx

            spec = cast(JsonType, ctx.outputs[KpmSpecificationOutputStage.name])
        except BuildException as e:
            logger.error(f"{e}")
            sys.exit(1)

        asyncio.run(
            KPM._run_client(
                kpm_run_client(
                    RPCparams(
                        host,
                        port,
                        spec,
                        build_dir,
                        ctx.top_module.design if ctx.top_module else None,
                        [*ctx.all_modules],
                        [*ctx.all_interfaces],
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

    try:
        pipeline = BuildPipeline.yaml_kpm_spec_pipeline(output)
        pipeline.run_files(list(files), design, Path())
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)


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

    try:
        pipeline = BuildPipeline.yaml_kpm_flow_pipeline(output)
        pipeline.run_files(list(files), design, Path())
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)
