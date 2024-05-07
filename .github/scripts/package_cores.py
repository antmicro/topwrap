# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path
from typing import List

from topwrap.repo.files import HttpGetFile
from topwrap.repo.user_repo import UserRepo, VerilogFileHandler


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


def package_cores():
    """Generates reusable cores package for usage in Topwrap project."""
    core_repo = UserRepo()

    for repo in repos:
        core_files = []
        for file in repo.sources:
            core_files.append(HttpGetFile(f"{repo.root_url}/{file}"))

        core_repo.add_files(VerilogFileHandler(core_files))

        Path(repo.name).mkdir(exist_ok=True)
        core_repo.save(repo.name)


if __name__ == "__main__":
    package_cores()
