# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from typing import Dict, List

import pytest

from topwrap.design import DesignDescription

from .common import read_json_file, read_yaml_file


@pytest.fixture
def ip_names() -> List[str]:
    return ["pwm", "hdmi", "hierarchy"]


@pytest.fixture
def pwm_ipcores_yamls() -> List[str]:
    _pwm_yamls_prefix = "examples/pwm/ipcores/"
    return [
        "topwrap/ips/axi/axi_axil_adapter.yaml",
        _pwm_yamls_prefix + "ps7.yaml",
        _pwm_yamls_prefix + "litex_pwm.yml",
    ]


@pytest.fixture
def hdmi_ipcores_yamls() -> List[str]:
    _hdmi_yamls_prefix = "examples/hdmi/ipcores/"
    _axi_yamls_prefix = "topwrap/ips/axi/"
    return [
        _hdmi_yamls_prefix + "axi_dispctrl.yaml",
        _hdmi_yamls_prefix + "clock_crossing.yaml",
        _hdmi_yamls_prefix + "dma_axi_in_axis_out.yaml",
        _hdmi_yamls_prefix + "hdmi_tx.yaml",
        _hdmi_yamls_prefix + "litex_mmcm.yaml",
        _hdmi_yamls_prefix + "proc_sys_reset.yaml",
        _hdmi_yamls_prefix + "ps7.yaml",
        _axi_yamls_prefix + "axi_axil_adapter.yaml",
        _axi_yamls_prefix + "axi_interconnect.yaml",
        _axi_yamls_prefix + "axi_protocol_converter.yaml",
        _axi_yamls_prefix + "axis_dwidth_converter.yaml",
        _axi_yamls_prefix + "axis_async_fifo.yaml",
    ]


@pytest.fixture
def hierarchy_ipcores_yamls() -> List[str]:
    _hierarchy_yamls_prefix = "examples/hierarchy/repo/cores/"
    return [
        _hierarchy_yamls_prefix + "c_mod_1/c_mod_1.yaml",
        _hierarchy_yamls_prefix + "c_mod_2/c_mod_2.yaml",
        _hierarchy_yamls_prefix + "c_mod_3/c_mod_3.yaml",
        _hierarchy_yamls_prefix + "s1_mod_1/s1_mod_1.yaml",
        _hierarchy_yamls_prefix + "s1_mod_2/s1_mod_2.yaml",
        _hierarchy_yamls_prefix + "s1_mod_3/s1_mod_3.yaml",
        _hierarchy_yamls_prefix + "s2_mod_1/s2_mod_1.yaml",
        _hierarchy_yamls_prefix + "s2_mod_2/s2_mod_2.yaml",
    ]


@pytest.fixture
def all_yaml_files(
    pwm_ipcores_yamls: List[str], hdmi_ipcores_yamls: List[str], hierarchy_ipcores_yamls: List[str]
) -> Dict[str, List[str]]:
    return {
        "pwm": pwm_ipcores_yamls,
        "hdmi": hdmi_ipcores_yamls,
        "hierarchy": hierarchy_ipcores_yamls,
    }


@pytest.fixture
def all_specification_files(ip_names: List[str]) -> Dict[str, dict]:
    return {
        ip_name: read_json_file(
            f"tests/data/data_kpm/examples/{ip_name}/specification_{ip_name}.json"
        )
        for ip_name in ip_names
    }


@pytest.fixture
def all_dataflow_files(ip_names: List[str]) -> Dict[str, dict]:
    return {
        ip_name: read_json_file(f"tests/data/data_kpm/examples/{ip_name}/{ip_name}_dataflow.json")
        for ip_name in ip_names
    }


@pytest.fixture
def all_designs(ip_names: List[str]) -> Dict[str, DesignDescription]:
    return {
        ip_name: read_yaml_file(f"tests/data/data_kpm/examples/{ip_name}/test_project.yml")
        for ip_name in ip_names
    }


@pytest.fixture
def all_encoded_design_files(all_designs: Dict[str, DesignDescription]) -> Dict[str, str]:
    return {
        test_name: b64encode(design.to_yaml().encode("utf-8")).decode("utf-8")
        for test_name, design in all_designs.items()
    }


@pytest.fixture
def pwm_specification(all_specification_files: Dict[str, dict]) -> dict:
    return all_specification_files["pwm"]


@pytest.fixture
def hdmi_specification(all_specification_files: Dict[str, dict]) -> dict:
    return all_specification_files["hdmi"]


@pytest.fixture
def hierarchy_specification(all_specification_files: Dict[str, dict]) -> dict:
    return all_specification_files["hierarchy"]


@pytest.fixture
def pwm_dataflow(all_dataflow_files: Dict[str, dict]) -> dict:
    return all_dataflow_files["pwm"]


@pytest.fixture
def hdmi_dataflow(all_dataflow_files: Dict[str, dict]) -> dict:
    return all_dataflow_files["hdmi"]


@pytest.fixture
def hierarchy_dataflow(all_dataflow_files: Dict[str, dict]) -> dict:
    return all_dataflow_files["hierarchy"]


@pytest.fixture
def pwm_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["pwm"]


@pytest.fixture
def hdmi_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["hdmi"]


@pytest.fixture
def hierarchy_design(all_designs: Dict[str, DesignDescription]) -> DesignDescription:
    return all_designs["hierarchy"]
