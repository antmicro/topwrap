# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict

import cyclopts
from prettytable import PrettyTable

cli = cyclopts.App()

MAIN_BRANCH = "main"


def get_coverage_per_file() -> Dict[str, int]:
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "-rs",
            "-k",
            "not round",
            "--cov-report=json",
            "--cov=topwrap",
            "--cov-config=pyproject.toml",
            "--cov-report=json:cover/coverage.json",
            "tests",
        ],
        check=False,
    )

    if result.returncode != 0:
        sys.exit(f"just exited with unexpected code {result.returncode}")

    with open("cover/coverage.json") as f:
        coverage = json.load(f)

    out = {}
    for file, entry in coverage["files"].items():
        out[file] = entry["summary"]["percent_covered"]
    return out


def get_coverage_on_main() -> Dict[str, int]:
    original_cwd = Path.cwd()

    with TemporaryDirectory() as tmpdir:
        shutil.copytree(original_cwd, tmpdir, dirs_exist_ok=True)
        os.chdir(tmpdir)
        try:
            subprocess.run(["git", "switch", MAIN_BRANCH, "--force"], check=True)
            return get_coverage_per_file()
        finally:
            os.chdir(original_cwd)


@cli.default
def coverage_check(print_coverage: bool = False):
    """Print coverage and check if there is regression.

    Parameters
    ----------
    print_coverage
         Print coverage of all files and diff from main branch.
    """
    print("Running coverage on current branch")
    coverage_on_current = get_coverage_per_file()
    print("Running coverage on main branch")
    coverage_on_main = get_coverage_on_main()

    files = set(coverage_on_current) | set(coverage_on_main)

    @dataclass
    class ReportCoverageItem:
        current: float
        main: float

    report_coverage: Dict[str, ReportCoverageItem] = {}
    regression = False

    for key in files:
        # There is new file in current branch
        if key not in coverage_on_main:
            report_coverage[key] = ReportCoverageItem(coverage_on_current[key], 0)
            continue

        # File was deleted or moved in current branch
        if key not in coverage_on_current:
            report_coverage[key] = ReportCoverageItem(0, coverage_on_main[key])
            continue

        # Coverage dropped, report that
        if coverage_on_main[key] > coverage_on_current[key]:
            regression = True

        report_coverage[key] = ReportCoverageItem(coverage_on_current[key], coverage_on_main[key])

    table = PrettyTable(["File", "Current branch [%]", "Main branch [%]", "Change [%]"])
    for file, item in sorted(
        report_coverage.items(), key=lambda entry: entry[1].current - entry[1].main, reverse=True
    ):
        table.add_row(
            [file, f"{item.current:.3f}", f"{item.main:.3f}", f"{(item.current - item.main):.3f}"]
        )

    if print_coverage:
        print(table)
    elif regression:
        sys.exit(1)


if __name__ == "__main__":
    cli()
