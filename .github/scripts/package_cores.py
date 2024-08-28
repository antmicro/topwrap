#!/usr/bin/env python3
# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""This module contains a `package_fusesoc` function and helpers. The goal of `package_fusesoc` is to
download, parse and package cores from fusesoc library to use as external repos for topwrap projects"""

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

import click

from topwrap.cli import parse_main
from topwrap.repo.file_handlers import VerilogFileHandler
from topwrap.repo.files import HttpGetFile
from topwrap.repo.user_repo import UserRepo

logger = logging.getLogger(__name__)


@dataclass
class RemoteRepo:
    name: str
    root_url: str
    sources: List[str]


repos = [
    RemoteRepo(
        name="vexriscv",
        root_url="https://raw.githubusercontent.com/litex-hub/pythondata-cpu-vexriscv/1979a644dbe64d8d32dfbdd970dccee6add63723/pythondata_cpu_vexriscv/verilog",
        sources=[
            "VexRiscv.v",
        ],
    ),
]


def package_repos():
    """Generates reusable cores package for usage in Topwrap project."""
    core_repo = UserRepo()

    for repo in repos:
        core_files = []
        for file in repo.sources:
            core_files.append(HttpGetFile(f"{repo.root_url}/{file}"))

        core_repo.add_files(VerilogFileHandler(core_files))

        Path(repo.name).mkdir(exist_ok=True)
        core_repo.save(repo.name)


@click.command()
@click.option("--log-level", required=False, default="INFO", help="Log level")
def package_cores(log_level: str):
    """Downloads, parses and packages fusesoc cores library to topwrap repos"""
    if log_level in ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.setLevel(log_level)
    else:
        logger.setLevel("INFO")
        logger.warning(f"incorrect log level {log_level}, using INFO instead")

    # creating workspace directory, making sure it is empty
    Path("build").mkdir(exist_ok=True)
    shutil.rmtree("build/fusesoc_workspace", ignore_errors=True)
    shutil.rmtree("build/export", ignore_errors=True)
    Path("build/fusesoc_workspace").mkdir(exist_ok=True)

    os.chdir("build/fusesoc_workspace")  # root/build/workspace
    subprocess.run(["fusesoc", "config", "cache_root", "cache_dir"], check=True)
    subprocess.run(
        ["fusesoc", "library", "add", "fusesoc-cores", "https://github.com/fusesoc/fusesoc-cores"],
        check=True,
    )

    os.chdir(
        "fusesoc_libraries/fusesoc-cores"
    )  # root/build/fusesoc_workspace/fusesoc_libraries/fusesoc-cores
    cores_str = [str(x) for x in Path(".").glob("*") if x.is_dir()]
    os.chdir("../..")  # root/build/fusesoc_workspace

    IGNORE_LIST = [
        ".git",
    ]
    FILE_IGNORE_LIST = [
        "tests",
    ]
    FILE_IGNORE_PATTERN_LIST = [
        re.compile(raw_regex)
        for raw_regex in [
            ".*_tb",
            ".*/test_.*",
            ".*_test",
            ".*/tb_.*",
            ".*/tst_.*",
            ".*bench/.*",
            ".*testbench.*",
        ]
    ]

    cores_downloaded: List[str] = []
    cores_failed = []
    for core in cores_str:
        if core in IGNORE_LIST:
            continue
        try:
            subprocess.run(["fusesoc", "fetch", core], check=True)
            cores_downloaded.append(core)
        except Exception as e:
            cores_failed.append(core)
            logger.warning(f"failed to fetch {core} due to {e}")
    logger.warning(f"failed to download {len(cores_failed)} cores: {cores_failed}")
    logger.warning(f"downloaded {len(cores_downloaded)} cores: {cores_downloaded}")

    # root/build/fusesoc_workspace/scratchpad - all hdl files
    Path("scratchpad").mkdir(exist_ok=True)
    # root/build/fusesoc_workspace/build - intermediate build dir
    Path("build").mkdir(exist_ok=True)

    os.chdir("cache_dir")  # root/build/fusesoc_workspace/cache_dir

    for c in [x for x in Path(".").rglob("*") if x.suffix in [".v", ".vh", ".vhd", ".vhdl"]]:
        shutil.copy(str(c), "../scratchpad/")

    error_counter = 0
    pass_counter = 0
    error_parses: List[str] = []
    full_good: List[str] = []

    # iterating over fusesoc cores, note that fusesoc core is a topwrap repo, not topwrap core
    for core in cores_downloaded:
        core_build_dir = "../../build/" + core
        # finding the path of a fusesoc core - they have a suffix with version
        for path in [x for x in Path(".").glob(core + "*")]:
            os.chdir(
                path
            )  # root/build/fusesoc_workspace/cache_dir/[core] - intermediate build dir for fusesoc core (repo)
            core_path_list = [
                x for x in Path(".").rglob("*") if x.suffix in [".v", ".vh", ".vhd", ".vhdl"]
            ]  # looking for hdl files
            if len(core_path_list) > 0:
                # root/build/fusesoc_workspace/build/[core] and workspace/build/[core]/cores
                Path(core_build_dir).mkdir(exist_ok=True)
                Path(core_build_dir + "/cores").mkdir(exist_ok=True)
                err_ini = error_counter
                # iterating over hdl files, cores in topwrap terminology
                for core_path in core_path_list:
                    if any(
                        compiled_reg.match(str(core_path))
                        for compiled_reg in FILE_IGNORE_PATTERN_LIST
                    ):
                        continue
                    if str(core_path.stem) in FILE_IGNORE_LIST:
                        continue
                    component_build_dir = core_build_dir + "/cores/" + str(core_path.stem)
                    # root/build/fusesoc_workspace/build/[core]/cores/[component] - intermediate build dir for topwrap core in a repo
                    Path(component_build_dir).mkdir(exist_ok=True)
                    logger.info(f"parsing {os.getcwd()} / {str(core_path)}")
                    # parsing core, first normally, then in scratchpad to resolve import errors
                    try:
                        with click.Context(parse_main) as ctx:
                            ctx.invoke(
                                parse_main,
                                use_yosys=False,
                                iface_deduce=False,
                                iface=(),
                                log_level=log_level,
                                files=[str(core_path)],
                                dest_dir=component_build_dir,
                            )
                        # root/build/fusesoc_workspace/build/[core]/cores/[component]/srcs - path for hdl file describing [component]
                        Path(component_build_dir + "/srcs").mkdir(exist_ok=True)
                        shutil.copy(str(core_path), component_build_dir + "/srcs")
                        pass_counter += 1
                    except Exception:
                        try:
                            with click.Context(parse_main) as ctx:
                                ctx.invoke(
                                    parse_main,
                                    use_yosys=False,
                                    iface_deduce=False,
                                    iface=(),
                                    log_level=log_level,
                                    files=[str(Path("../../scratchpad/" + core_path.name))],
                                    dest_dir=component_build_dir,
                                )
                            # root/build/fusesoc_workspaces/build/[core]/cores/[component]/srcs - path for hdl file describing [component]
                            Path(component_build_dir + "/srcs").mkdir(exist_ok=True)
                            shutil.copy(str(core_path), component_build_dir + "/srcs")
                            pass_counter += 1
                        except Exception as e2:
                            logger.warning(f"failed to parse due to {e2}")
                            error_counter += 1
                            error_parses.append(core + "/" + str(core_path))
                            subprocess.run(["ls"], check=True)
                            subprocess.run(["pwd"], check=True)
                # check if whole fusesoc core parsed correctly
                if error_counter == err_ini:
                    full_good.append(core)
            os.chdir("..")  # root/build/fusesoc_workspace/cache_dir
    for succ_core in full_good:
        shutil.copytree(
            Path("../build") / Path(succ_core),
            Path("../../export") / Path(succ_core),
            dirs_exist_ok=True,
        )
    os.chdir("../..")  # root/build
    logger.warning(f"parses failed: {error_counter} out of {error_counter+pass_counter}")
    logger.warning(error_parses)
    logger.info(f"fully well parsed cores are {full_good} - a total of {len(full_good)}")

    os.chdir("export")
    logger.info("packaging cores")
    package_repos()


if __name__ == "__main__":
    package_cores()
    os.chdir("export")
    package_repos()
