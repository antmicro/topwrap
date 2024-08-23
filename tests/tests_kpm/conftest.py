# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from typing import Dict, List

import pytest

from topwrap.design import DesignDescription

from .common import TEST_DATA_PATH, read_json_file, read_yaml_file


def ip_names_data():
    return ["pwm", "hdmi", "hierarchy"]


@pytest.fixture
def ip_names() -> List[str]:
    return ip_names_data()


def pwm_ipcores_yamls_data() -> List[str]:
    _pwm_yamls_prefix = "examples/pwm/ipcores/"
    return [
        "topwrap/ips/axi/axi_axil_adapter.yaml",
        _pwm_yamls_prefix + "ps7.yaml",
        _pwm_yamls_prefix + "litex_pwm.yml",
    ]


@pytest.fixture
def pwm_ipcores_yamls() -> List[str]:
    return pwm_ipcores_yamls_data()


def hdmi_ipcores_yamls_data() -> List[str]:
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
def hdmi_ipcores_yamls() -> List[str]:
    return hdmi_ipcores_yamls_data()


def hierarchy_ipcores_yamls_data() -> List[str]:
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
def hierarchy_ipcores_yamls() -> List[str]:
    return hierarchy_ipcores_yamls_data()


def all_yaml_files_data() -> Dict[str, List[str]]:
    return {
        "pwm": pwm_ipcores_yamls_data(),
        "hdmi": hdmi_ipcores_yamls_data(),
        "hierarchy": hierarchy_ipcores_yamls_data(),
    }


@pytest.fixture
def all_yaml_files() -> Dict[str, List[str]]:
    return all_yaml_files_data()


def all_specification_files_data() -> Dict[str, dict]:
    return {
        ip_name: read_json_file(f"{TEST_DATA_PATH}{ip_name}/specification_{ip_name}.json")
        for ip_name in ip_names_data()
    }


@pytest.fixture
def all_specification_files() -> Dict[str, dict]:
    return all_specification_files_data()


def all_dataflow_files_data() -> Dict[str, dict]:
    return {
        ip_name: read_json_file(f"{TEST_DATA_PATH}{ip_name}/dataflow_{ip_name}.json")
        for ip_name in ip_names_data()
    }


@pytest.fixture
def all_dataflow_files() -> Dict[str, dict]:
    return all_dataflow_files_data()


def all_designs_data() -> Dict[str, DesignDescription]:
    return {
        ip_name: read_yaml_file(f"{TEST_DATA_PATH}{ip_name}/project_{ip_name}.yml")
        for ip_name in ip_names_data()
    }


@pytest.fixture
def all_designs() -> Dict[str, DesignDescription]:
    return all_designs_data()


def all_examples_designs_data() -> Dict[str, DesignDescription]:
    return {
        ip_name: read_yaml_file(f"examples/{ip_name}/project.yml") for ip_name in ip_names_data()
    }


@pytest.fixture
def all_examples_designs() -> Dict[str, DesignDescription]:
    return all_examples_designs_data()


def all_encoded_design_files_data() -> Dict[str, str]:
    return {
        test_name: b64encode(design.to_yaml().encode("utf-8")).decode("utf-8")
        for test_name, design in all_designs_data().items()
    }


@pytest.fixture
def all_encoded_design_files() -> Dict[str, str]:
    return all_encoded_design_files_data()


@pytest.fixture
def pwm_specification() -> dict:
    return all_specification_files_data()["pwm"]


@pytest.fixture
def hdmi_specification() -> dict:
    return all_specification_files_data()["hdmi"]


@pytest.fixture
def hierarchy_specification() -> dict:
    return all_specification_files_data()["hierarchy"]


@pytest.fixture
def pwm_dataflow() -> dict:
    return all_dataflow_files_data()["pwm"]


@pytest.fixture
def hdmi_dataflow() -> dict:
    return all_dataflow_files_data()["hdmi"]


@pytest.fixture
def hierarchy_dataflow() -> dict:
    return all_dataflow_files_data()["hierarchy"]


@pytest.fixture
def pwm_design() -> DesignDescription:
    return all_designs_data()["pwm"]


@pytest.fixture
def hdmi_design() -> DesignDescription:
    return all_designs_data()["hdmi"]


@pytest.fixture
def hierarchy_design() -> DesignDescription:
    return all_designs_data()["hierarchy"]
