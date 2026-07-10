# Copyright (c) 2023-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""Run pyright, optionally failing if any file's error count is higher than on the main branch."""

import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

import cyclopts
from prettytable import PrettyTable

cli = cyclopts.App()

MAIN_BRANCH = "main"

ErrorCounts = dict[str, int]


def count_errors() -> tuple[ErrorCounts, ErrorCounts]:
    errortypes: ErrorCounts = defaultdict(int)
    errorfiles: ErrorCounts = defaultdict(int)

    result = subprocess.run(
        ["pyright", "--outputjson"],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"pyright exited with unexpected code {result.returncode}")

    errors_data = json.loads(result.stdout)
    for diagnostic in errors_data["generalDiagnostics"]:
        errortypes[diagnostic.get("rule", "unknown")] += 1
        file = str(Path(diagnostic["file"]).relative_to(Path.cwd()))
        errorfiles[file] += 1

    return errortypes, errorfiles


def count_errors_on_main() -> tuple[ErrorCounts, ErrorCounts]:
    pyproject_origin = Path.cwd() / "pyproject.toml"
    original_cwd = Path.cwd()

    with TemporaryDirectory() as tmpdir:
        shutil.copytree(original_cwd, tmpdir, dirs_exist_ok=True)
        os.chdir(tmpdir)
        try:
            subprocess.run(["git", "switch", MAIN_BRANCH, "--force"], check=True)
            # keep the branch's pyright config so both runs are comparable
            shutil.copy(pyproject_origin, "pyproject.toml")
            return count_errors()
        finally:
            os.chdir(original_cwd)


def print_table(
    header: list[str],
    columns: int,
    errors: ErrorCounts,
    errors_main: ErrorCounts,
) -> None:
    table = PrettyTable(header[:columns])
    for name, num in sorted(errors.items(), key=lambda x: x[1], reverse=True):
        table.add_row([name, num, num - errors_main[name]][:columns])
    print(table)


@cli.default
def pyright_check(*, compare: bool = False):
    errortypes, errorfiles = count_errors()

    errortypes_main: ErrorCounts = defaultdict(int)
    errorfiles_main: ErrorCounts = defaultdict(int)

    if compare:
        errortypes_main, errorfiles_main = count_errors_on_main()

        for errtype in errortypes_main:
            errortypes.setdefault(errtype, 0)
        for file in errorfiles_main:
            errorfiles.setdefault(file, 0)

    subprocess.run(["pyright"])

    columns = 3 if compare else 2
    print_table(["Error", "Count", "Change"], columns, errortypes, errortypes_main)
    print_table(["File", "Errors", "Change"], columns, errorfiles, errorfiles_main)

    if compare:
        regressed = [file for file, num in errorfiles.items() if num - errorfiles_main[file] > 0]
        if regressed:
            sys.exit(f"pyright found new errors compared to {MAIN_BRANCH} in: {', '.join(regressed)}")


if __name__ == "__main__":
    cli()
