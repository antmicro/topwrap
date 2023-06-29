# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
import jsonschema
from yaml import load, Loader

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from fpga_topwrap.kpm_topwrap_client import _ipcore_names_to_yamls_mapping
from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from fpga_topwrap.kpm_common import *


@pytest.fixture
def hdmi_ipcores_yamls() -> list:
    _hdmi_yamls_prefix = 'examples/hdmi/ipcores/'
    _axi_yamls_prefix = 'fpga_topwrap/ips/axi/'
    return [
        _hdmi_yamls_prefix + 'axi_dispctrl.yaml',
        _hdmi_yamls_prefix + 'clock_crossing.yaml',
        _hdmi_yamls_prefix + 'dma_axi_in_axis_out.yaml',
        _hdmi_yamls_prefix + 'hdmi_tx.yaml',
        _hdmi_yamls_prefix + 'litex_mmcm.yaml',
        _hdmi_yamls_prefix + 'proc_sys_reset.yaml',
        _hdmi_yamls_prefix + 'ps7.yaml',
        _axi_yamls_prefix + 'axi_axil_adapter.yaml',
        _axi_yamls_prefix + 'axi_interconnect.yaml',
        _axi_yamls_prefix + 'axi_protocol_converter.yaml',
        _axi_yamls_prefix + 'axis_dwidth_converter.yaml',
        _axi_yamls_prefix + 'axis_async_fifo.yaml',
    ]


@pytest.fixture
def hdmi_ipcores_names_to_yamls(hdmi_ipcores_yamls) -> dict:
    return _ipcore_names_to_yamls_mapping(hdmi_ipcores_yamls)


@pytest.fixture
def hdmi_design_yaml() -> dict:
    with open('examples/hdmi/project.yml', 'r') as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def hdmi_specification(hdmi_ipcores_yamls) -> dict:
    return ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)


@pytest.fixture
def hdmi_dataflow(hdmi_design_yaml, hdmi_specification) -> dict:
    return kpm_dataflow_from_design_descr(hdmi_design_yaml, hdmi_specification)


def test_hdmi_specification_generation(hdmi_specification, specification_schema):
    assert len(hdmi_specification['nodes']) == 14 # 12 IP cores + 2 External metanodes
    jsonschema.validate(hdmi_specification, specification_schema)


def test_hdmi_dataflow_import(hdmi_dataflow):
    # check number of imported nodes (15 + 8 external metanodes)
    assert len(hdmi_dataflow['graph']['nodes']) == 23

    # check number of imported externals
    num_dataflow_externals = len(get_dataflow_metanodes(hdmi_dataflow))
    assert num_dataflow_externals == 8

    # check connections between ip cores
    num_dataflow_ip_conns = len(get_dataflow_ip_connections(hdmi_dataflow))
    assert num_dataflow_ip_conns == 59

    # check overrode {'value': ..., 'width': ...} parameter value
    axi_interconnect_node = [node for node in hdmi_dataflow['graph']['nodes'] if node['name'] == 'axi_interconnect0'][0]
    m_addr_width_prop = [prop for prop in axi_interconnect_node['properties'] if prop['name'] == 'M_ADDR_WIDTH'][0]
    assert m_addr_width_prop['value'] == '96\'h100000001000000010'
