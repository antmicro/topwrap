# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
import yaml

import topwrap.cli.main  # noqa: F401 - register CLI commands
from topwrap.cli import cli
from topwrap.cli.package import _collect_sources
from topwrap.library import library_contents


def run_cli(*tokens: str):
    return cli.meta(list(tokens), result_action="return_value", exit_on_error=True)


def load_core(path: Path) -> dict:
    _, yaml_body = path.read_text().split("\n", 1)
    return yaml.safe_load(yaml_body)


def test_package_core_preserves_include_dirs_and_defines(tmp_path: Path):
    output = tmp_path / "cores" / "widget"
    include_dir = output / "rtl" / "include"
    include_dir.mkdir(parents=True)
    (include_dir / "config.svh").write_text("// Package include file.\n")

    source = output / "rtl" / "widget.sv"
    source.write_text(
        """`include "config.svh"
module widget(input logic [`WIDTH-1:0] data);
endmodule
"""
    )

    run_cli(
        "package",
        str(source),
        f"+incdir+{include_dir}",
        "+define+WIDTH=8",
        "+define+ENABLE_STATUS",
        "--lib",
        "--output",
        str(output),
    )

    core = load_core(output / "widget.core")
    rtl_files = core["filesets"]["rtl"]["files"]
    header = next(entry for entry in rtl_files if "config.svh" in next(iter(entry)))
    header_attrs = next(iter(header.values()))

    assert header_attrs["is_include_file"] is True
    assert header_attrs["include_path"].endswith("rtl/include")
    parameters = core["parameters"]
    assert parameters["WIDTH"] == {
        "datatype": "int",
        "paramtype": "vlogdefine",
        "default": 8,
    }
    assert parameters["ENABLE_STATUS"] == {
        "datatype": "bool",
        "paramtype": "vlogdefine",
        "default": True,
    }
    assert core["targets"]["default"]["parameters"] == ["WIDTH", "ENABLE_STATUS"]
    modules, _ = library_contents("packaged", str(output))
    assert modules == ["vendor:libdefault:widget:0.1"]


def test_package_core_rejects_sources_outside_output(tmp_path: Path):
    source = tmp_path / "widget.sv"
    source.write_text("module widget; endmodule\n")
    output = tmp_path / "package"

    with pytest.raises(SystemExit):
        run_cli("package", str(source), "--lib", "--output", str(output))

    assert not output.exists()


def test_filelist_accepts_multiple_tokens_and_inline_comments(tmp_path: Path):
    first = tmp_path / "first.sv"
    second = tmp_path / "second.sv"
    first.touch()
    second.touch()
    filelist = tmp_path / "sources.f"
    filelist.write_text("first.sv second.sv +define+WIDTH=8 // inputs\n")

    files, _, defines = _collect_sources((), (filelist,))

    assert files == [first, second]
    assert defines == ["WIDTH=8"]


def test_filelist_cycle_is_reported(tmp_path: Path):
    filelist = tmp_path / "recursive.f"
    filelist.write_text("-f recursive.f\n")

    with pytest.raises(ValueError, match="recursive filelist reference"):
        _collect_sources((), (filelist,))
