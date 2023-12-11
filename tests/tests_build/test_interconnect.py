# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestInterconnect:
    @pytest.mark.skipif(
        sys.version_info[:2] < (3, 9) or sys.version_info[:2] > (3, 10),
        reason="interconnect test requires Python 3.9 or 3.10 due to litex requiring Python 3.9 or 3.10",
    )
    @pytest.mark.skipif(
        not (
            shutil.which("verilator")
            and shutil.which("riscv64-unknown-elf-gcc")
            and shutil.which("make")
            and shutil.which("meson")
            and shutil.which("ninja")
            and shutil.which("hexdump")
        ),
        reason="verilator, riscv64-unknown-elf toolchain, make, meson, ninja and hexdump are required to run the interconnect test",
    )
    def test_interconnect_design(self, request: pytest.FixtureRequest) -> None:
        remote_url = "https://github.com/antmicro/soc-generator.git"
        commit_sha = "76ac5b3743bea1bb6e5d2ac7ecae31ab39d5e8b3"
        data_dir = request.path.parent / Path("../data/data_build/interconnect")
        # don't change formatting of the context manager below - this formatting is needed
        # for Python 3.8 compatibility, see https://bugs.python.org/issue12782
        # fmt: off
        with (
            tempfile.TemporaryDirectory()
        ) as repo_tmp_dir, (
            tempfile.TemporaryDirectory()
        ) as build_tmp_dir:
            # fmt: on
            repo_dir = Path(repo_tmp_dir)
            build_dir = Path(build_tmp_dir)
            example_dir = repo_dir / Path("examples/simple_soc")
            # clone soc generator repo
            subprocess.check_call(["git", "clone", "--recurse-submodules", remote_url, repo_dir])
            subprocess.check_call(["git", "checkout", commit_sha], cwd=repo_dir)
            subprocess.check_call(["pip", "install", "."], cwd=repo_dir)
            subprocess.check_call(["pip", "install", "-r", "requirements.txt"], cwd=example_dir)
            subprocess.check_call(["make", "deps"], cwd=example_dir)

            # build topwrap design
            subprocess.check_call(
                [
                    "python",
                    "-m",
                    "fpga_topwrap",
                    "build",
                    "-d",
                    "project.yml",
                    "-b",
                    build_dir,
                    "-p",
                    "xc7k70tfbg484",
                ],
                cwd=data_dir,
            )

            # include additional sources in topwrap design
            subprocess.check_call(
                [
                    "sh",
                    "-c",
                    f"cat {data_dir}/sources/mem.v {data_dir}/sources/soc.v {data_dir}/sources/crg.v >> {build_dir}/top.v",
                ]
            )

            # move topwrap design to the location expected by soc generator
            subprocess.check_call(["mkdir", example_dir / "build"])
            subprocess.check_call(["cp", build_dir / "top.v", example_dir / "build" / "top.v"])

            # create an empty file that soc generator expects
            subprocess.check_call(["touch", example_dir / "build" / "wishbone_interconnect.v"])

            # run simulation
            output = subprocess.check_output(["make", "sim-run"], cwd=example_dir).decode("utf-8")

            # tx_data is a list of all bytes transmitted on TX (in hex, as strings)
            tx_data = re.findall(r"(?:\[\d+\] TX: (0x[0-9a-fA-F]+) RX: 0x[0-9a-fA-F]+\n)", output)
            # check that "hello world" was transmitted on UART TX
            assert "".join(map(lambda v: chr(int(v, base=16)), tx_data)) == "hello world"
