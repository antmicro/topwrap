# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import asyncio
import logging
import multiprocessing
import os
import queue
import shutil
import subprocess
import sys
import threading
import webbrowser
from enum import Enum
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import IO, Any, Callable, Coroutine, Optional, Tuple, Union, cast

import rich.console
from cyclopts.types import ExistingDirectory, ExistingFile

from topwrap.cli import cli
from topwrap.config_defaults import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_DIR,
    DEFAULT_SERVER_ADDR,
    DEFAULT_SERVER_PORT,
    DEFAULT_WORKSPACE_DIR,
)
from topwrap.kpm_common import RPCparams
from topwrap.kpm_topwrap_client import kpm_run_client
from topwrap.plugin.base import BuildException
from topwrap.plugin.pipeline import BuildPipeline, OutputDir
from topwrap.plugin.steps import KpmSpecificationOutputStage
from topwrap.repo.files import DEFAULT_GIT_CACHE_DIR
from topwrap.util import JsonType, get_config

logger = logging.getLogger(__name__)


def main():
    cli.meta(console=rich.console.Console(no_color=True))


@cli.command(name="build")
def build_main(
    *,
    sources: Tuple[ExistingDirectory, ...] = (),
    design: ExistingFile,
    build_dir: Optional[Path] = None,
    gensrc_dir: Optional[Path] = None,
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

    if gensrc_dir is None:
        gensrc_dir = Path(build_dir)

    get_config().force_interface_compliance = iface_compliance

    outdir = OutputDir(build_dir, gensrc_dir)

    try:
        pipeline = BuildPipeline.yaml_sv_pipeline(
            fuse=fuse, fuse_part=part, fuse_src_dirs=list(sources)
        )
        pipeline.run_files([], design, outdir)
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)


def _run_pipeline_manager_main(argv: list[str], write_conn: Optional[Connection] = None) -> None:
    if write_conn is not None:
        os.dup2(write_conn.fileno(), sys.stdout.fileno())
        os.dup2(write_conn.fileno(), sys.stderr.fileno())

    from pipeline_manager.__main__ import main

    sys.argv = argv
    sys.exit(main())


class _PipelineManagerProcess:
    """Runs pipeline_manager either via subprocess.Popen or, if
    preserve_parent_state, via a spawned multiprocessing.Process (needed so
    the child inherits sys.path). POSIX-only in the latter case.

    If capture_logs is False, output is left to print directly to the
    terminal instead of being captured into .logs."""

    def __init__(
        self, args: list[str], preserve_parent_state: bool, capture_logs: bool = False
    ) -> None:
        self._read_conn: Optional[Connection] = None
        self.process: Union[subprocess.Popen[bytes], BaseProcess]
        self.logs: Optional[IO[bytes]] = None
        if preserve_parent_state:
            write_conn = None
            if capture_logs:
                self._read_conn, write_conn = multiprocessing.Pipe(duplex=False)
            self.process = multiprocessing.get_context("spawn").Process(
                target=_run_pipeline_manager_main, args=(args, write_conn)
            )
            self.process.start()
            if write_conn is not None:
                write_conn.close()
            if self._read_conn is not None:
                self.logs = os.fdopen(os.dup(self._read_conn.fileno()), "rb")
            self._wait: Callable[..., Any] = self.process.join
        else:
            self.process = subprocess.Popen(
                [sys.executable, "-m", *args],
                stdout=subprocess.PIPE if capture_logs else None,
                stderr=subprocess.STDOUT if capture_logs else None,
            )
            if capture_logs:
                assert self.process.stdout is not None
                self.logs = self.process.stdout
            self._wait = self.process.wait

    @property
    def returncode(self) -> Optional[int]:
        if isinstance(self.process, subprocess.Popen):
            return self.process.returncode
        return self.process.exitcode

    def terminate(self) -> None:
        self.process.terminate()

    def wait(self, timeout: Optional[float] = None) -> None:
        try:
            self._wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            raise RuntimeError(
                f"{self.process} did not terminate within {timeout}s, killed it"
            ) from None

    def close(self) -> None:
        if self.logs is not None:
            self.logs.close()
        if self._read_conn is not None:
            self._read_conn.close()


class KPM:
    child_processes: list[_PipelineManagerProcess] = []
    kpm_run_client_task: Optional[asyncio.Task[Any]] = None

    @staticmethod
    def cleanup():
        error: Optional[Exception] = None
        for child in KPM.child_processes:
            child.terminate()
            try:
                child.wait(timeout=5)
            except RuntimeError as e:
                error = e
        if KPM.kpm_run_client_task:
            KPM.kpm_run_client_task.cancel()
        if error is not None:
            raise error

    @staticmethod
    def build_server(preserve_parent_state: bool, **params_dict: Any):
        args = ["pipeline_manager", "build", "server-app"]
        for k, v in params_dict.items():
            Path(v).mkdir(exist_ok=True, parents=True)
            args += [f"--{k}".replace("_", "-"), f"{v}"]

        proc = _PipelineManagerProcess(args, preserve_parent_state)
        proc.wait()
        if proc.returncode:
            raise RuntimeError(f"pipeline_manager build failed with exit code {proc.returncode}")

    @staticmethod
    def run_server(
        preserve_parent_state: bool,
        server_ready_event: Optional[threading.Event] = None,
        show_kpm_logs: bool = True,
        shutdown_server: bool = False,
        **params_dict: Any,
    ):
        args = ["pipeline_manager", "run"]
        for k, v in params_dict.items():
            args += [f"--{k}".replace("_", "-"), f"{v}"]

        child = _PipelineManagerProcess(args, preserve_parent_state, capture_logs=True)
        assert child.logs is not None
        KPM.child_processes.append(child)

        server_ready_string = "Uvicorn running on"
        try:
            while server_logs := child.logs.readline().decode("utf-8"):
                if server_ready_event is not None and server_ready_string in server_logs:
                    server_ready_event.set()
                    if shutdown_server:
                        child.terminate()
                if show_kpm_logs:
                    sys.stdout.write(server_logs)
            else:
                logging.warning("KPM server has been terminated")
                if server_ready_event is not None and not server_ready_event.is_set():
                    logging.warning(
                        "Make sure that there isn't any instance of pipeline manager running in"
                        " the background"
                    )
                    raise Exception("Failed to initialize KPM server")
        finally:
            child.close()

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
                        list(yamlfiles),
                        ctx.positions,
                        design,
                    ),
                    client_ready_event,
                )
            )
        )

    @staticmethod
    async def _run_client(coro: Coroutine[None, None, None]):
        KPM.kpm_run_client_task = asyncio.create_task(coro)
        await KPM.kpm_run_client_task


@cli.command(name="ipxact_gen")
def generate_ipxact(
    design: ExistingFile,
    build_dir: Optional[Path] = None,
    iface_compliance: bool = False,
):
    """Generate IP-XACT 2022 files from a top design YAML file.

    Parameters
    ---------
    design
        Top design file.
    build_dir
        Output directory for generated files.
    iface_compliance
        Force intterfdace compliance checking.
    """
    if build_dir is None:
        build_dir = Path("build")

    get_config().force_interface_compliance = iface_compliance

    try:
        pipeline = BuildPipeline.yaml_ipxact_pipeline()
        pipeline.run_files([], design, build_dir)
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)


@cli.command(name="kpm_client")
def kpm_client_main(
    yamlfiles: Tuple[ExistingFile, ...] = (),
    *,
    host: str = DEFAULT_SERVER_ADDR,
    port: int = DEFAULT_SERVER_PORT,
    design: Optional[ExistingFile] = None,
    build_dir: Optional[Path] = None,
    gensrc_dir: Optional[Path] = None,
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
    preserve_parent_state: bool = False,
):
    """Build KPM server"""
    if workspace_directory is None:
        workspace_directory = Path(get_config().kpm_build_location) / DEFAULT_WORKSPACE_DIR

    if output_directory is None:
        output_directory = Path(get_config().kpm_build_location) / DEFAULT_FRONTEND_DIR

    KPM.build_server(
        workspace_directory=workspace_directory,
        output_directory=output_directory,
        preserve_parent_state=preserve_parent_state,
    )


@cli.command(name="kpm_run_server")
def kpm_run_server(
    frontend_directory: Optional[ExistingDirectory] = None,
    server_host: str = DEFAULT_SERVER_ADDR,
    server_port: int = DEFAULT_SERVER_PORT,
    backend_host: str = DEFAULT_BACKEND_ADDR,
    backend_port: int = DEFAULT_BACKEND_PORT,
    verbosity: str = "INFO",
    preserve_parent_state: bool = False,
):
    """Run a KPM server"""
    if frontend_directory is None:
        frontend_directory = Path(get_config().kpm_build_location) / DEFAULT_FRONTEND_DIR

    try:
        KPM.run_server(
            frontend_directory=frontend_directory,
            preserve_parent_state=preserve_parent_state,
            server_host=server_host,
            server_port=server_port,
            backend_host=backend_host,
            backend_port=backend_port,
            verbosity=verbosity,
        )
    except Exception as e:
        logging.error(f"{e}")
    finally:
        KPM.cleanup()


class CacheTarget(str, Enum):
    GIT = "git"
    KPM_BUILD = "kpm-build"
    ALL = "all"


def _cache_dirs(target: Optional[CacheTarget]) -> dict[CacheTarget, Path]:
    dirs = {
        CacheTarget.GIT: DEFAULT_GIT_CACHE_DIR,
        CacheTarget.KPM_BUILD: Path(get_config().kpm_build_location),
    }
    if target is None or target is CacheTarget.ALL:
        return dirs
    return {target: dirs[target]}


@cli.command(name="clean-cache")
def clean_cache(*, target: Optional[CacheTarget] = None):
    """Remove locally cached files created by topwrap.

    Parameters
    ----------
    target
        Which cache to remove: 'git' removes cached clones of repositories loaded via the
        'git:' resource scheme, 'kpm-build' removes the cached Pipeline Manager build,
        'all' removes every cache. If omitted, all caches are removed.
    """
    for name, cache_dir in _cache_dirs(target).items():
        if not cache_dir.exists():
            logger.info(f"No '{name.value}' cache found at '{cache_dir}'")
            continue
        shutil.rmtree(cache_dir)
        logger.info(f"Removed '{name.value}' cache at '{cache_dir}'")


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
    preserve_parent_state: bool = False,
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
    preserve_parent_state
        Use a spawned multiprocessing.Process instead of a plain subprocess
        to run pipeline_manager. Needed under packaging setups
        where a bare subprocess doesn't inherit sys.path. POSIX-only.
    """

    if frontend_directory is None:
        frontend_directory = Path(get_config().kpm_build_location) / DEFAULT_FRONTEND_DIR

    if workspace_directory is None:
        workspace_directory = Path(get_config().kpm_build_location) / DEFAULT_WORKSPACE_DIR

    logging.info("Checking if server is built")
    if (not frontend_directory.exists() or not workspace_directory.exists()) and use_server:
        logging.info("Server build is incomplete, building now")
        KPM.build_server(
            workspace_directory=workspace_directory,
            output_directory=frontend_directory,
            preserve_parent_state=preserve_parent_state,
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
                "preserve_parent_state": preserve_parent_state,
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
    finally:
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
