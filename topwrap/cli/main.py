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
from typing import IO, Annotated, Any, Callable, Coroutine, Optional, Tuple, Union, cast

import rich.console
from cyclopts import Parameter
from cyclopts.types import ExistingDirectory, ExistingFile

from topwrap.cli import cli
from topwrap.config_defaults import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_BACKEND_PORT,
    DEFAULT_SERVER_ADDR,
    DEFAULT_SERVER_PORT,
)
from topwrap.kpm_common import RPCparams
from topwrap.kpm_topwrap_client import kpm_run_client
from topwrap.plugin.base import BuildException, OutputDir
from topwrap.plugin.pipeline import BuildPipeline
from topwrap.plugin.steps import KpmSpecificationOutputStage
from topwrap.repo.files import DEFAULT_GIT_CACHE_DIR
from topwrap.util import JsonType, get_config, warn_deprecated

logger = logging.getLogger(__name__)


def main():
    cli.meta(console=rich.console.Console())


@cli.command(name="build", show=False)
def build_main(
    *,
    sources: Annotated[
        Tuple[ExistingDirectory, ...], Parameter(alias="-s", negative="--empty-sources")
    ] = (),
    design: Annotated[ExistingFile, Parameter(alias="-d")],
    build_dir: Annotated[Optional[Path], Parameter(alias="-b")] = None,
    gensrc_dir: Annotated[Optional[Path], Parameter(alias="-g")] = None,
    fuse: Annotated[bool, Parameter(alias="-f", negative="--no-fuse")] = False,
    part: Annotated[Optional[str], Parameter(alias="-p")] = None,
    iface_compliance: Annotated[
        bool, Parameter(alias="-i", negative="--no-iface-compliance")
    ] = False,
):
    """Generate SystemVerilog from a top design YAML file.

    .. deprecated:: 1.0.0

    Parameters
    ----------
    sources
        Directories to scan for additional sources.
    design
        Top design file.
    build_dir
        Output build directory.
    gensrc_dir
        Output directory for generated files (defaults to --build-dir).
    fuse
        Generate a FuseSoC .core file for further synthesis.
    part
        FPGA part number (ignored without --fuse).
    iface_compliance
        Force interface compliance checking.
    """
    warn_deprecated(
        "the 'build' command is deprecated and will be removed in 1.0.0; use 'generate'"
    )

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


@cli.command(name="generate")
def generate_main(
    design: ExistingFile,
    /,
    *,
    target_dir: Annotated[Path, Parameter(alias="-t")] = Path("build"),
    sources: Annotated[
        Tuple[ExistingDirectory, ...], Parameter(alias="-s", negative="--empty-sources")
    ] = (),
    fusesoc: bool = False,
    part: Annotated[Optional[str], Parameter(alias="-p")] = None,
    ipxact: bool = False,
    diagram: bool = False,
    specification: bool = False,
    iface_compliance: bool = False,
):
    """Generate SystemVerilog from a top design YAML file.

    Parameters
    ----------
    design
        Top design file.
    target_dir
        Target directory.
    sources
        Directories containing additional HDL or constraint sources for the
        generated FuseSoC core.
    fusesoc
        Generate a FuseSoC .core file for further synthesis.
    part
        FPGA part number used by the generated FuseSoC target.
    ipxact
        Generate IP-XACT 2022 files.
    diagram
        Generate a KPM dataflow diagram.
    specification
        Generate a KPM specification file.
    iface_compliance
        Force interface compliance checking.
    """
    gensrc_dir = Path(target_dir) / Path("src")

    get_config().force_interface_compliance = iface_compliance

    outdir = OutputDir(target_dir, gensrc_dir)

    try:
        pipeline = BuildPipeline.yaml_sv_pipeline(
            fuse=fusesoc,
            fuse_part=part,
            fuse_src_dirs=list(sources),
        )
        pipeline.run_files([], design, outdir)
        if ipxact:
            pipeline = BuildPipeline.yaml_ipxact_pipeline()
            pipeline.run_files([], design, outdir)
        if diagram:
            pipeline = BuildPipeline.yaml_kpm_flow_pipeline(target_dir / "kpm_dataflow.json")
            pipeline.run_files([], design, outdir)
        if specification:
            pipeline = BuildPipeline.yaml_kpm_spec_pipeline(target_dir / "kpm_spec.json")
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
    def run_server(
        preserve_parent_state: bool,
        server_ready_event: Optional[threading.Event] = None,
        show_kpm_logs: bool = True,
        shutdown_server: bool = False,
        **params_dict: Any,
    ):
        args = ["pipeline_manager", "run"]
        for k, v in params_dict.items():
            flag = f"--{k}".replace("_", "-")
            if isinstance(v, bool):
                if v:
                    args.append(flag)
            else:
                args += [flag, f"{v}"]

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


@cli.command(name="ipxact_gen", show=False)
def generate_ipxact(
    design: Annotated[ExistingFile, Parameter(alias="-d")],
    build_dir: Annotated[Optional[Path], Parameter(alias="-b")] = None,
    gensrc_dir: Annotated[Optional[Path], Parameter(alias="-g")] = None,
    iface_compliance: Annotated[
        bool, Parameter(alias="-i", negative="--no-iface-compliance")
    ] = False,
):
    """Generate IP-XACT 2022 files from a top design YAML file.

    Parameters
    ---------
    design
        Top design file.
    build_dir
        Output build directory.
    gensrc_dir
        Output directory for generated files (defaults to --build-dir).
    iface_compliance
        Force intterfdace compliance checking.
    """
    if build_dir is None:
        build_dir = Path("build")
    if gensrc_dir is None:
        gensrc_dir = Path(build_dir)

    outdir = OutputDir(build_dir, gensrc_dir)

    get_config().force_interface_compliance = iface_compliance

    try:
        pipeline = BuildPipeline.yaml_ipxact_pipeline()
        pipeline.run_files([], design, outdir)
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)


@cli.command(name="kpm_client", show=False)
def kpm_client_main(
    yamlfiles: Annotated[
        Tuple[ExistingFile, ...], Parameter(alias="-y", negative="--empty-yamlfiles")
    ] = (),
    *,
    host: Annotated[str, Parameter(alias="-H")] = DEFAULT_SERVER_ADDR,
    port: Annotated[int, Parameter(alias="-p")] = DEFAULT_SERVER_PORT,
    design: Annotated[Optional[ExistingFile], Parameter(alias="-d")] = None,
    build_dir: Annotated[Optional[Path], Parameter(alias="-b")] = None,
):
    """Run a client app that connects to a running KPM server.

    .. deprecated:: 1.0.0

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


@cli.command(name="kpm_run_server", show=False)
def kpm_run_server(
    server_host: Annotated[str, Parameter(alias="-s")] = DEFAULT_SERVER_ADDR,
    server_port: Annotated[int, Parameter(alias="-S")] = DEFAULT_SERVER_PORT,
    backend_host: Annotated[str, Parameter(alias="-b")] = DEFAULT_BACKEND_ADDR,
    backend_port: Annotated[int, Parameter(alias="-B")] = DEFAULT_BACKEND_PORT,
    verbosity: Annotated[str, Parameter(alias="-v")] = "INFO",
    preserve_parent_state: Annotated[
        bool, Parameter(alias="-p", negative="--no-preserve-parent-state")
    ] = False,
    follow_symlink: Annotated[bool, Parameter(alias="-f", negative="--no-follow-symlink")] = False,
):
    """Run a KPM server using Pipeline Manager's bundled frontend.

    .. deprecated:: 1.0.0
    """
    try:
        KPM.run_server(
            preserve_parent_state=preserve_parent_state,
            server_host=server_host,
            server_port=server_port,
            backend_host=backend_host,
            backend_port=backend_port,
            verbosity=verbosity,
            follow_symlink=follow_symlink,
        )
    except Exception as e:
        logging.error(f"{e}")
        sys.exit(1)
    finally:
        KPM.cleanup()


class CacheTarget(str, Enum):
    GIT = "git"
    ALL = "all"


def _cache_dirs(target: Optional[CacheTarget]) -> dict[CacheTarget, Path]:
    dirs = {
        CacheTarget.GIT: DEFAULT_GIT_CACHE_DIR,
    }
    if target is None or target is CacheTarget.ALL:
        return dirs
    return {target: dirs[target]}


@cli.command(name="clean-cache")
def clean_cache(*, target: Annotated[Optional[CacheTarget], Parameter(alias="-t")] = None):
    """Remove locally cached files created by topwrap.

    Parameters
    ----------
    target
        Which cache to remove: 'git' removes cached clones of repositories loaded via the
        'git:' resource scheme; 'all' removes every cache. If omitted, all caches are removed.
    """
    for name, cache_dir in _cache_dirs(target).items():
        if not cache_dir.exists():
            logger.info(f"No '{name.value}' cache found at '{cache_dir}', skipping")
            continue
        shutil.rmtree(cache_dir)
        logger.info(f"Removed '{name.value}' cache at '{cache_dir}'")


@cli.command(name="gui")
def topwrap_gui(
    yamlfiles: Annotated[
        Tuple[ExistingFile, ...], Parameter(alias="-y", negative="--empty-yamlfiles")
    ] = (),
    *,
    design: Annotated[Optional[ExistingFile], Parameter(alias="-d")] = None,
    server_host: Annotated[str, Parameter(alias="-s")] = DEFAULT_SERVER_ADDR,
    server_port: Annotated[int, Parameter(alias="-S")] = DEFAULT_SERVER_PORT,
    backend_host: Annotated[str, Parameter(alias="-b")] = DEFAULT_BACKEND_ADDR,
    backend_port: Annotated[int, Parameter(alias="-B")] = DEFAULT_BACKEND_PORT,
    use_server: Annotated[bool, Parameter(negative="--no-use-server")] = True,
    raise_exception: Annotated[
        bool, Parameter(alias="-r", negative="--no-raise-exception")
    ] = False,
    preserve_parent_state: Annotated[
        bool, Parameter(alias="-p", negative="--no-preserve-parent-state")
    ] = False,
    follow_symlink: Annotated[bool, Parameter(alias="-f", negative="--no-follow-symlink")] = False,
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
    follow_symlink
        Follow symlinks when serving the frontend's static files. Needed
        when the frontend directory, or files within it, are only
        reachable through symlinks, e.g. under a Bazel-managed install.
    """

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
                "show_kpm_logs": True,
                "server_host": server_host,
                "server_port": server_port,
                "backend_host": backend_host,
                "backend_port": backend_port,
                "preserve_parent_state": preserve_parent_state,
                "follow_symlink": follow_symlink,
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
        sys.exit(1)
    finally:
        KPM.cleanup()


@cli.command(name="specification", show=False)
def generate_kpm_spec(
    files: Annotated[
        Tuple[ExistingFile, ...], Parameter(alias="-f", negative="--empty-files")
    ] = (),
    *,
    design: Annotated[Optional[ExistingFile], Parameter(alias="-d")] = None,
    output: Annotated[Optional[Path], Parameter(alias="-o")] = None,
    hidden_layers: Tuple[str, ...] = (),
):
    """Generate KPM specification from IP core YAMLs"""

    if output is None:
        output = Path("kpm_spec.json")

    try:
        pipeline = BuildPipeline.yaml_kpm_spec_pipeline(output, hidden_layers=hidden_layers)
        pipeline.run_files(list(files), design, OutputDir(Path(), Path()))
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)


@cli.command(name="dataflow", show=False)
def generate_kpm_design(
    files: Annotated[
        Tuple[ExistingFile, ...], Parameter(alias="-f", negative="--empty-files")
    ] = (),
    *,
    design: Annotated[ExistingFile, Parameter(alias="-d")],
    output: Annotated[Optional[Path], Parameter(alias="-o")] = None,
    hidden_layers: Tuple[str, ...] = (),
):
    """Generate KPM dataflow from IP core YAMLs and a design YAML"""

    if output is None:
        output = Path("kpm_dataflow.json")

    try:
        pipeline = BuildPipeline.yaml_kpm_flow_pipeline(output, hidden_layers=hidden_layers)
        pipeline.run_files(list(files), design, OutputDir(Path(), Path()))
    except BuildException as e:
        logger.error(f"{e}")
        sys.exit(1)
