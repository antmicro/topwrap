#!/usr/bin/env python3
# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""This module contains a `package_fusesoc` function and helpers. The goal of `package_fusesoc` is
to download, parse and package cores from fusesoc library to use as external repos for topwrap
projects"""

import logging
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import click
import yaml
from pyslang import DiagnosticSeverity

from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.model.misc import Identifier
from topwrap.repo.user_repo import Core, UserRepo
from topwrap.resource_field import FileReferenceHandler
from topwrap.util import ExistsStrategy

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
    default="INFO",
    show_default=True,
    help="Log level",
)
@click.argument("save_path", type=click.Path(file_okay=False, path_type=Path))
def package_cores(log_level: str, save_path: Path):
    """Downloads, parses and packages fusesoc cores library to topwrap repos"""
    logging.basicConfig(level=log_level)
    logging.getLogger().setLevel(log_level)

    save_path = save_path.absolute()
    tmpdir_ctx = TemporaryDirectory()
    tmpdir = Path(tmpdir_ctx.name)

    os.chdir(tmpdir)

    subprocess.run(["fusesoc", "config", "cache_root", "cache_dir"], check=True)
    subprocess.run(
        ["fusesoc", "library", "add", "fusesoc-cores", "https://github.com/fusesoc/fusesoc-cores"],
        check=True,
    )

    cores_downloaded: list[str] = []
    cores_failed = []

    for core_file in Path("fusesoc_libraries/fusesoc-cores").rglob("*.core"):
        data = yaml.safe_load(core_file.read_text())
        if (core_name := data.get("name")) is None:
            continue
        try:
            subprocess.run(["fusesoc", "fetch", core_name], check=True)
            cores_downloaded.append(core_name)
        except Exception as e:
            cores_failed.append(core_name)
            logger.warning(f"failed to fetch {core_name} due to {e}")

    logger.warning(f"failed to download {len(cores_failed)} cores: {cores_failed}")
    logger.warning(f"downloaded {len(cores_downloaded)} cores: {cores_downloaded}")

    sv_exts = SystemVerilogFrontend().metadata.file_association

    repo = UserRepo("fusesoc_cores")

    for dir in Path("cache_dir").iterdir():
        frontend = SystemVerilogFrontend(diag_level=DiagnosticSeverity.Fatal)
        sv_sources = [
            p for p in dir.rglob("*") if p.suffix.lower() in sv_exts and not p.is_symlink()
        ]

        if len(sv_sources) == 0:
            continue

        try:
            [*modules] = frontend.parse_files(sv_sources)
            for mod in modules:
                mod.id = Identifier(name=mod.id.name, vendor="", library="fusesoc")
                repo.add_resource(
                    Core(
                        f"fusesoc_{mod.id.name}",
                        top_level_name=mod.id.name,
                        sources=[FileReferenceHandler(p.file) for p in mod.refs],
                    ),
                    ExistsStrategy.SKIP,
                )
        except Exception:
            logger.error("Failed to parse FuseSoC core '%s'", dir.name, exc_info=True)
            continue

        logger.info("Successfully parsed FuseSoC core '%s'", dir.name)

    save_path.mkdir(exist_ok=True, parents=True)
    repo.save(save_path / "fusesoc_repo")

    tmpdir_ctx.cleanup()


if __name__ == "__main__":
    package_cores()
