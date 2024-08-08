# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import pytest
from yaml import Loader, load

from .common import read_json_file


@pytest.fixture
def pwm_design_yaml() -> dict:
    with open("examples/pwm/project.yml", "r") as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def hdmi_design_yaml() -> dict:
    with open("examples/hdmi/project.yml", "r") as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def hierarchy_design_yaml() -> dict:
    with open("examples/hierarchy/design.yaml", "r") as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def pwm_ipcores_yamls() -> list:
    _pwm_yamls_prefix = "examples/pwm/ipcores/"
    return [
        "topwrap/ips/axi/axi_axil_adapter.yaml",
        _pwm_yamls_prefix + "ps7.yaml",
        _pwm_yamls_prefix + "litex_pwm.yml",
    ]


@pytest.fixture
def hdmi_ipcores_yamls() -> list:
    _hdmi_yamls_prefix = "examples/hdmi/ipcores/"
    _axi_yamls_prefix = "axi/"
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
def hierarchy_ipcores_yamls() -> list:
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
def pwm_specification() -> dict:
    return read_json_file("tests/data/data_kpm/specification_pwm.json")


@pytest.fixture
def pwm_dataflow() -> dict:
    return read_json_file("tests/data/data_kpm/pwm_dataflow.json")


@pytest.fixture
def hdmi_specification() -> dict:
    return read_json_file("tests/data/data_kpm/specification_hdmi.json")


@pytest.fixture
def hdmi_dataflow() -> dict:
    return read_json_file("tests/data/data_kpm/hdmi_dataflow.json")


@pytest.fixture
def hierarchy_specification() -> dict:
    return read_json_file("tests/data/data_kpm/specification_hierarchy.json")


@pytest.fixture
def hierarchy_dataflow() -> dict:
    return read_json_file("tests/data/data_kpm/hierarchy_dataflow.json")
