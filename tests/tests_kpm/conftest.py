# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from pathlib import Path
from typing import Dict

import pytest

from topwrap.design import DesignDescription
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


def all_designs_data() -> Dict[str, DesignDescription]:
    data = {}
    for ip_name, dir in test_dirs_data().items():
        if dir.parts[-2] == "examples":
            data[ip_name] = DesignDescription.load(Path("examples") / ip_name / "project.yaml")
        else:
            data[ip_name] = DesignDescription.load(dir / f"project_{ip_name}.yaml")

    return data


@pytest.fixture
def all_designs() -> Dict[str, DesignDescription]:
    return all_designs_data()


@pytest.fixture
def all_encoded_design_files(all_designs: Dict[str, DesignDescription]) -> Dict[str, str]:
    return {
        test_name: b64encode(design.to_yaml().encode("utf-8")).decode("utf-8")
        for test_name, design in all_designs.items()
    }


@pytest.fixture
def pwm_specification(all_specification_files: Dict[str, JsonType]) -> JsonType:
    return all_specification_files["pwm"]


@pytest.fixture
def hdmi_specification(all_specification_files: Dict[str, JsonType]) -> JsonType:
    return all_specification_files["hdmi"]


@pytest.fixture
def hierarchy_specification(all_specification_files: Dict[str, JsonType]) -> JsonType:
    return all_specification_files["hierarchy"]


@pytest.fixture
def complex_specification(all_specification_files: Dict[str, JsonType]) -> JsonType:
    return all_specification_files["complex"]


@pytest.fixture
def pwm_dataflow(all_dataflow_files: Dict[str, JsonType]) -> JsonType:
    return all_dataflow_files["pwm"]


@pytest.fixture
def hdmi_dataflow(all_dataflow_files: Dict[str, JsonType]) -> JsonType:
    return all_dataflow_files["hdmi"]


@pytest.fixture
def hierarchy_dataflow(all_dataflow_files: Dict[str, JsonType]) -> JsonType:
    return all_dataflow_files["hierarchy"]


@pytest.fixture
def complex_dataflow(all_dataflow_files: Dict[str, JsonType]) -> JsonType:
    return all_dataflow_files["complex"]


@pytest.fixture
def pwm_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["pwm"]


@pytest.fixture
def hdmi_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["hdmi"]


@pytest.fixture
def hierarchy_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["hierarchy"]


@pytest.fixture
def complex_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["complex"]
