# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from os import cpu_count
from pathlib import Path

import yaml

from topwrap.fuse_helper import (
    CORE_FILE_DESCRIPTION,
    FuseSocBuilder,
    FuseSocFlowApi,
    FuseSocHook,
    FuseSocTarget,
    FuseSocToolApi,
    SourceFile,
)
from topwrap.model.misc import Identifier


class TestFuseSoc:
    def test_default_output(self, tmp_path: Path):
        fuse = FuseSocBuilder(part="vivado_part")

        fuse.add_source(Path("top.v"), "verilogSource")

        # Use the temporary directory fixture
        filepath = tmp_path / "top.core"
        fuse.build("top", filepath, [])

        # Read back
        src = filepath.read_text()

        # Remove the .core header
        src = src.removeprefix("CAPI=2:\n")
        obj = yaml.full_load(src)

        assert isinstance(obj, dict), "the core file should be a dict"

        assert obj == {
            "name": "::top",
            "description": CORE_FILE_DESCRIPTION,
            "filesets": {
                "rtl": {
                    "files": [
                        {"top.v": {"file_type": "verilogSource"}},
                    ],
                },
            },
            "targets": {
                "default": {
                    "filesets": ["rtl"],
                    "toplevel": "top",
                    "hooks": {
                        "pre_build": ["set_jobs"],
                    },
                    "default_tool": "vivado",
                    "tools": {
                        "vivado": {
                            "part": "vivado_part",
                        },
                    },
                },
            },
            "scripts": {
                "set_jobs": {
                    "cmd": [
                        "sed",
                        "-i",
                        f'"s/launch_runs synth_1/launch_runs synth_1 -jobs {cpu_count()}/g"',
                        "top_0_synth.tcl",
                    ]
                },
            },
        }

    def test_default_output_empty(self, tmp_path: Path):
        fuse = FuseSocBuilder(None)

        fuse.add_source(Path("top.v"), "verilogSource")

        # remove generated vivado default target
        fuse.set_generate_vivado(False)

        # Use the temporary directory fixture
        filepath = tmp_path / "top.core"
        fuse.build("top", filepath, [])

        # Read back
        src = filepath.read_text()

        # Remove the .core header
        src = src.removeprefix("CAPI=2:\n")
        obj = yaml.full_load(src)

        assert isinstance(obj, dict), "the core file should be a dict"

        assert obj == {
            "name": "::top",
            "description": CORE_FILE_DESCRIPTION,
            "filesets": {
                "rtl": {
                    "files": [
                        {"top.v": {"file_type": "verilogSource"}},
                    ],
                },
            },
        }

    def test_dependency(self, tmp_path: Path):
        fuse = FuseSocBuilder(None)

        fuse.add_source(Path("top.v"), "verilogSource")
        fuse.add_dependency("vendor:library:name:version")
        fuse.add_dependency("vendor:library:no_version")
        fuse.add_dependency("::only_name")
        fuse.add_dependency("vendor::name:version")

        # remove generated vivado default target
        fuse.set_generate_vivado(False)

        # Use the temporary directory fixture
        filepath = tmp_path / "top.core"
        fuse.build("top", filepath, [])

        # Read back
        src = filepath.read_text()

        # Remove the .core header
        src = src.removeprefix("CAPI=2:\n")
        obj = yaml.full_load(src)

        assert isinstance(obj, dict), "the core file should be a dict"

        assert obj == {
            "name": "::top",
            "description": CORE_FILE_DESCRIPTION,
            "filesets": {
                "rtl": {
                    "files": [
                        {"top.v": {"file_type": "verilogSource"}},
                    ],
                    "depend": [
                        "vendor:library:name:version",
                        "vendor:library:no_version",
                        "::only_name",
                        "vendor::name:version",
                    ],
                },
            },
        }

    def test_fileset(self, tmp_path: Path):
        fuse = FuseSocBuilder(None)

        fuse.add_source(Path("top.v"), "verilogSource")
        fuse.add_fileset(
            name="custom_fileset",
            files=[SourceFile(Path("custom.sv"), "systemVerilogSource")],
            depends=[
                Identifier("name", "vendor", "library", "version"),
                Identifier("no_version", "vendor", "library", ""),
            ],
        )
        fuse.set_generate_vivado(False)

        # Use the temporary directory fixture
        filepath = tmp_path / "top.core"
        fuse.build("top", filepath, [])

        # Read back
        src = filepath.read_text()

        # Remove the .core header
        src = src.removeprefix("CAPI=2:\n")
        obj = yaml.full_load(src)

        assert isinstance(obj, dict), "the core file should be a dict"

        assert obj == {
            "name": "::top",
            "description": CORE_FILE_DESCRIPTION,
            "filesets": {
                "rtl": {
                    "files": [
                        {"top.v": {"file_type": "verilogSource"}},
                    ],
                },
                "custom_fileset": {
                    "files": [
                        {"custom.sv": {"file_type": "systemVerilogSource"}},
                    ],
                    "depend": [
                        "vendor:library:name:version",
                        "vendor:library:no_version",
                    ],
                },
            },
        }

    def test_tool_api(self, tmp_path: Path):
        fuse = FuseSocBuilder(None)

        fuse.add_source(Path("top.v"), "verilogSource")
        fuse.set_generate_vivado(False)

        fuse.add_target(
            FuseSocTarget(
                "target_name",
                "top",
                FuseSocToolApi(
                    default_tool="default_tool_name",
                    tools={
                        "default_tool_name": {
                            "string_option": "string_value",
                            "number_option": 123,
                            "list_option": ["1", 2],
                            "dict_option": {"1": 2},
                        }
                    },
                ),
                filesets=["rtl"],
                hooks=[
                    FuseSocHook("pre_build", ["script0"]),
                ],
            )
        )

        fuse.add_script("script0", ["a", "b", "c"])

        # Use the temporary directory fixture
        filepath = tmp_path / "top.core"
        fuse.build("top", filepath, [])

        # Read back
        src = filepath.read_text()

        # Remove the .core header
        src = src.removeprefix("CAPI=2:\n")
        obj = yaml.full_load(src)

        assert isinstance(obj, dict), "the core file should be a dict"

        assert obj == {
            "name": "::top",
            "description": CORE_FILE_DESCRIPTION,
            "filesets": {
                "rtl": {
                    "files": [
                        {"top.v": {"file_type": "verilogSource"}},
                    ],
                },
            },
            "targets": {
                "target_name": {
                    "toplevel": "top",
                    "default_tool": "default_tool_name",
                    "filesets": ["rtl"],
                    "tools": {
                        "default_tool_name": {
                            "string_option": "string_value",
                            "number_option": 123,
                            "list_option": ["1", 2],
                            "dict_option": {"1": 2},
                        },
                    },
                    "hooks": {
                        "pre_build": ["script0"],
                    },
                },
            },
            "scripts": {
                "script0": {
                    "cmd": ["a", "b", "c"],
                }
            },
        }

    def test_flow_api(self, tmp_path: Path):
        fuse = FuseSocBuilder(None)

        fuse.add_source(Path("top.v"), "verilogSource")
        fuse.set_generate_vivado(False)

        fuse.add_target(
            FuseSocTarget(
                "target_name",
                "top",
                FuseSocFlowApi(
                    type="flow_type",
                    options={
                        "string_option": "string_value",
                        "number_option": 123,
                        "list_option": ["1", 2],
                        "dict_option": {"1": 2},
                    },
                    make_options=["make", "options"],
                ),
                filesets=["rtl"],
                hooks=[],  # we tested this in another test
            )
        )

        # Use the temporary directory fixture
        filepath = tmp_path / "top.core"
        fuse.build("top", filepath, [])

        # Read back
        src = filepath.read_text()

        # Remove the .core header
        src = src.removeprefix("CAPI=2:\n")
        obj = yaml.full_load(src)

        assert isinstance(obj, dict), "the core file should be a dict"

        assert obj == {
            "name": "::top",
            "description": CORE_FILE_DESCRIPTION,
            "filesets": {
                "rtl": {
                    "files": [
                        {"top.v": {"file_type": "verilogSource"}},
                    ],
                },
            },
            "targets": {
                "target_name": {
                    "toplevel": "top",
                    "filesets": ["rtl"],
                    "flow": "flow_type",
                    "flow_options": {
                        "string_option": "string_value",
                        "number_option": 123,
                        "list_option": ["1", 2],
                        "dict_option": {"1": 2},
                        "flow_make_options": ["make", "options"],
                    },
                },
            },
        }
