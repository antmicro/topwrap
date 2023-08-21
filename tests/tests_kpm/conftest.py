# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import pytest
from yaml import Loader, load
from tests.common import read_json_file


@pytest.fixture
def specification_schema_path() -> Path:
    specification_schema_path = "kenning-pipeline-manager/pipeline_manager/resources/schemas/unresolved_specification_schema.json"  # noqa: E501
    return Path(specification_schema_path)


@pytest.fixture
def specification_schema(specification_schema_path) -> dict:
    return read_json_file(specification_schema_path)


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
def pwm_ipcores_yamls() -> list:
    return [
        "fpga_topwrap/ips/axi/axi_axil_adapter.yaml",
        "examples/pwm/ipcores/ps7.yaml",
        "examples/pwm/ipcores/litex_pwm.yml",
    ]


@pytest.fixture
def hdmi_ipcores_yamls() -> list:
    _hdmi_yamls_prefix = "examples/hdmi/ipcores/"
    _axi_yamls_prefix = "fpga_topwrap/ips/axi/"
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
def pwm_dataflow() -> dict:
    return read_json_file("tests/data/data_kpm/pwm_dataflow.json")


@pytest.fixture
def hdmi_dataflow() -> dict:
    return read_json_file("tests/data/data_kpm/hdmi_dataflow.json")
