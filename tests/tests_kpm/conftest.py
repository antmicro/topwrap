# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from pathlib import Path
from typing import Dict

import pytest

from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.util import JsonType, read_json_file


def test_dirs_data() -> Dict[str, Path]:
    COMMON = "tests/data/data_kpm/"
    paths = {}
    for glob in (COMMON + "examples/*", COMMON + "conversions/*"):
        for path in Path(".").glob(glob):
            ip_name = path.stem
            paths[ip_name] = path
    return paths


@pytest.fixture
def test_dirs() -> Dict[str, Path]:
    return test_dirs_data()


@pytest.fixture
def all_specification_files(test_dirs: Dict[str, Path]) -> Dict[str, JsonType]:
    return {
        ip_name: read_json_file(dir / f"specification_{ip_name}.json")
        for ip_name, dir in test_dirs.items()
    }


@pytest.fixture
def all_dataflow_files(test_dirs: Dict[str, Path]) -> Dict[str, JsonType]:
    return {
        ip_name: read_json_file(dir / f"dataflow_{ip_name}.json")
        for ip_name, dir in test_dirs.items()
    }


def all_design_paths() -> Dict[str, Path]:
    data = {}
    for ip_name, dir in test_dirs_data().items():
        if dir.parts[-2] == "examples":
            data[ip_name] = Path("examples") / ip_name / "project.yaml"
        else:
            data[ip_name] = dir / f"project_{ip_name}.yaml"

    return data


@pytest.fixture
def all_design_files() -> Dict[str, str]:
    return {name: file.read_text() for name, file in all_design_paths().items()}


@pytest.fixture
def all_design_specifications() -> Dict[str, JsonType]:
    specs = {}

    frontend = YamlFrontend()
    for name, design in all_design_paths().items():
        spec = KpmSpecificationBackend.default()
        design_module = next(frontend.parse_files([design]))
        spec.add_module(design_module, recursive=True)
        specs[name] = spec.build()

    return specs


@pytest.fixture
def all_encoded_design_files(all_design_files: Dict[str, str]) -> Dict[str, str]:
    return {
        test_name: b64encode(design.encode("utf-8")).decode("utf-8")
        for test_name, design in all_design_files.items()
    }
