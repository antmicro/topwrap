# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
import yaml

import topwrap.cli.main  # noqa: F401 - register CLI commands
from topwrap.cli import cli, load_interfaces_from_repos
from topwrap.cli.package import _collect_sources
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.library import clear_index_cache, library_contents, module_index
from topwrap.util import get_config


def run_cli(*tokens: str):
    return cli.meta(list(tokens), result_action="return_value", exit_on_error=True)


def load_core(path: Path) -> dict:
    _, yaml_body = path.read_text().split("\n", 1)
    return yaml.safe_load(yaml_body)


def test_loaded_interfaces_are_unique_by_vlnv():
    interface_ids = [interface.id for interface in load_interfaces_from_repos()]

    assert len(interface_ids) == len(set(interface_ids))


def test_package_core_preserves_include_dirs_and_defines(tmp_path: Path):
    output = tmp_path / "cores" / "widget"
    include_dir = output
    include_dir.mkdir(parents=True)
    (include_dir / "config.svh").write_text("// Package include file.\n")
    (output / "widget.core").write_text("stale generated output\n")

    source = output / "widget.sv"
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
    source_attrs = next(entry["widget.sv"] for entry in rtl_files if "widget.sv" in entry)
    header = next(entry for entry in rtl_files if "config.svh" in next(iter(entry)))
    header_attrs = next(iter(header.values()))

    assert "is_include_file" not in source_attrs
    assert {next(iter(entry)) for entry in rtl_files} == {"widget.sv", "config.svh"}
    assert header_attrs["is_include_file"] is True
    assert header_attrs["include_path"] == "."
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


def test_package_rejects_vlnv_name_outside_output(tmp_path: Path):
    source = tmp_path / "widget.sv"
    source.write_text("module widget; endmodule\n")
    output = tmp_path / "package"

    with pytest.raises(SystemExit):
        run_cli(
            "package",
            str(source),
            "--output",
            str(output),
            "--vlnv",
            "vendor:library:../escaped:1.0",
        )

    assert not (tmp_path / "escaped.yaml").exists()


def test_package_saves_only_new_interface_definitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "package"
    output.mkdir()
    source = output / "widget.sv"
    known_source = "interface known_if; logic ready; modport manager(output ready); endinterface"
    source.write_text(
        known_source
        + "\ninterface new_if; logic valid; modport manager(output valid); endinterface"
        + "\nmodule widget(new_if.manager stream); endmodule\n"
    )
    known = SystemVerilogFrontend().parse_str([known_source]).interfaces[0]
    monkeypatch.setattr("topwrap.cli.package.load_interfaces_from_repos", lambda: iter([known]))

    run_cli("package", str(source), "--lib", "--output", str(output))

    core = load_core(output / "widget.core")
    files = {
        name: attrs["file_type"]
        for entry in core["filesets"]["topwrap"]["files"]
        for name, attrs in entry.items()
    }
    assert files == {
        "widget.yaml": "topwrapModule",
        "vendor_libdefault_new_if_0.1.yaml": "topwrapInterface",
    }
    monkeypatch.setitem(get_config().libraries, "packaged", str(output))
    clear_index_cache()
    try:
        module = IPCoreDescriptionFrontend().parse_file(
            module_index()["vendor:libdefault:widget:0.1"]
        )
        assert module.interfaces[0].definition.id.name == "new_if"
    finally:
        clear_index_cache()


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
