# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from pathlib import Path
from typing import Dict, List

import pytest

from topwrap.design import DesignDescription
from topwrap.util import JsonType, read_json_file


def pwm_ipcores_yamls_data() -> List[Path]:
    _pwm_yamls_prefix = Path("examples/pwm/ipcores/")
    return [
        Path("topwrap/ips/axi/axi_axil_adapter.yaml"),
        _pwm_yamls_prefix / "ps7.yaml",
        _pwm_yamls_prefix / "litex_pwm.yaml",
    ]


@pytest.fixture
def pwm_ipcores_yamls() -> List[Path]:
    return pwm_ipcores_yamls_data()


def hdmi_ipcores_yamls_data() -> List[Path]:
    _hdmi_yamls_prefix = Path("examples/hdmi/ipcores/")
    _axi_yamls_prefix = Path("topwrap/ips/axi/")
    return [
        _hdmi_yamls_prefix / "axi_dispctrl.yaml",
        _hdmi_yamls_prefix / "clock_crossing.yaml",
        _hdmi_yamls_prefix / "dma_axi_in_axis_out.yaml",
        _hdmi_yamls_prefix / "hdmi_tx.yaml",
        _hdmi_yamls_prefix / "litex_mmcm.yaml",
        _hdmi_yamls_prefix / "proc_sys_reset.yaml",
        _hdmi_yamls_prefix / "ps7.yaml",
        _axi_yamls_prefix / "axi_axil_adapter.yaml",
        _axi_yamls_prefix / "axi_interconnect.yaml",
        _axi_yamls_prefix / "axi_protocol_converter.yaml",
        _axi_yamls_prefix / "axis_dwidth_converter.yaml",
        _axi_yamls_prefix / "axis_async_fifo.yaml",
    ]


@pytest.fixture
def hdmi_ipcores_yamls() -> List[Path]:
    return hdmi_ipcores_yamls_data()


def hierarchy_ipcores_yamls_data() -> List[Path]:
    _hierarchy_yamls_prefix = Path("examples/hierarchy/repo/cores/")
    return [
        _hierarchy_yamls_prefix / "c_mod_1/c_mod_1.yaml",
        _hierarchy_yamls_prefix / "c_mod_2/c_mod_2.yaml",
        _hierarchy_yamls_prefix / "c_mod_3/c_mod_3.yaml",
        _hierarchy_yamls_prefix / "s1_mod_1/s1_mod_1.yaml",
        _hierarchy_yamls_prefix / "s1_mod_2/s1_mod_2.yaml",
        _hierarchy_yamls_prefix / "s1_mod_3/s1_mod_3.yaml",
        _hierarchy_yamls_prefix / "s2_mod_1/s2_mod_1.yaml",
        _hierarchy_yamls_prefix / "s2_mod_2/s2_mod_2.yaml",
    ]


@pytest.fixture
def hierarchy_ipcores_yamls() -> List[Path]:
    return hierarchy_ipcores_yamls_data()


def all_yaml_files_data() -> Dict[str, List[Path]]:
    return {
        "pwm": pwm_ipcores_yamls_data(),
        "hdmi": hdmi_ipcores_yamls_data(),
        "hierarchy": hierarchy_ipcores_yamls_data(),
        "complex": hierarchy_ipcores_yamls_data(),
    }


@pytest.fixture
def all_yaml_files() -> Dict[str, List[Path]]:
    return all_yaml_files_data()


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


@pytest.fixture
def all_designs(test_dirs: Dict[str, Path]) -> Dict[str, DesignDescription]:
    return {
        ip_name: DesignDescription.load(dir / f"project_{ip_name}.yaml")
        for ip_name, dir in test_dirs.items()
    }


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
