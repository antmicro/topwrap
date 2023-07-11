# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
import jsonschema
from yaml import load, Loader

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from fpga_topwrap.kpm_topwrap_client import _ipcore_names_to_yamls_mapping
from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from fpga_topwrap.kpm_dataflow_validator import (
    CheckStatus,
    _check_duplicate_ip_names,
    _check_ambigous_ports,
    _check_ext_in_to_ext_out_connections,
    _check_parameters_values,
    _check_unconnected_ports_interfaces
)
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
    assert len(hdmi_specification['nodes']) == 15 # 12 IP cores + 3 External metanodes
    jsonschema.validate(hdmi_specification, specification_schema)


class TestHDMIDataflowImport:
    @pytest.fixture
    def kpm_nodes(self, hdmi_design_yaml, hdmi_specification):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_nodes_from_design_descr
        return [node for node in kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)]

    @pytest.fixture
    def kpm_metanodes(self, hdmi_design_yaml):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_metanodes_from_design_descr
        return [node for node in kpm_metanodes_from_design_descr(hdmi_design_yaml)]

    def test_hdmi_nodes(self, kpm_nodes):
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == 15
        # check overrode {'value': ..., 'width': ...} parameter value
        axi_interconnect_node = [node for node in nodes_json if node['name'] == 'axi_interconnect0'][0]
        m_addr_width = [prop for prop in axi_interconnect_node['properties'] if prop['name'] == 'M_ADDR_WIDTH'][0]
        assert m_addr_width['value'] == '96\'h100000001000000010'

    def test_hdmi_metanodes(self, kpm_metanodes):
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]
        assert len(metanodes_json) == 8

    def test_hdmi_connections(self, hdmi_design_yaml, kpm_nodes):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_connections_from_design_descr
        connections = kpm_connections_from_design_descr(hdmi_design_yaml, kpm_nodes)
        assert len(connections) == 59

    def test_hdmi_metanodes_connections(self, hdmi_design_yaml, kpm_nodes, kpm_metanodes):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_metanodes_connections_from_design_descr
        connections = kpm_metanodes_connections_from_design_descr(hdmi_design_yaml, kpm_nodes, kpm_metanodes)
        assert len(connections) == 8


class TestHDMIDataflowExport:
    def test_parameters(self, hdmi_dataflow):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_properties_to_parameters
        axi_node = [node for node in hdmi_dataflow['graph']['nodes'] if node['name'] == 'axi_interconnect0'][0]
        parameters = _kpm_properties_to_parameters(axi_node['properties'])
        assert parameters['ADDR_WIDTH'] == 32
        assert parameters['M_ADDR_WIDTH'] == {'value': int("0x100000001000000010", 16), 'width': 96}

    def test_nodes_to_ips(self, hdmi_design_yaml, hdmi_dataflow, hdmi_ipcores_names_to_yamls):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_nodes_to_ips
        ips = _kpm_nodes_to_ips(hdmi_dataflow, hdmi_ipcores_names_to_yamls)
        assert ips.keys() == hdmi_design_yaml['ips'].keys()

    def test_port_interfaces(self, hdmi_design_yaml, hdmi_dataflow, hdmi_specification):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_connections_to_ports_ifaces
        connections = _kpm_connections_to_ports_ifaces(hdmi_dataflow, hdmi_specification)
        assert connections['interfaces'] == hdmi_design_yaml['interfaces']

    def test_externals(self, hdmi_design_yaml, hdmi_dataflow, hdmi_specification):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_connections_to_external
        assert _kpm_connections_to_external(hdmi_dataflow, hdmi_specification) == {
            'ports': {
                'hdmi': {
                    'HDMI_CLK_P': 'HDMI_CLK_P',
                    'HDMI_CLK_N': 'HDMI_CLK_N',
                    'HDMI_D0_P': 'HDMI_D0_P',
                    'HDMI_D0_N': 'HDMI_D0_N',
                    'HDMI_D1_P': 'HDMI_D1_P',
                    'HDMI_D1_N': 'HDMI_D1_N',
                    'HDMI_D2_P': 'HDMI_D2_P',
                    'HDMI_D2_N': 'HDMI_D2_N'
                }
            },
            'interfaces': {},
            'external': {
                'ports': {
                    'in': [],
                    'out': [
                        'HDMI_CLK_P',
                        'HDMI_CLK_N',
                        'HDMI_D0_P',
                        'HDMI_D0_N',
                        'HDMI_D1_P',
                        'HDMI_D1_N',
                        'HDMI_D2_P',
                        'HDMI_D2_N'
                    ],
                    'inout': []
                },
                'interfaces': {
                    'in': [],
                    'out': [],
                    'inout': []
                }
            }
        }


@pytest.mark.parametrize('_check_function, expected_result', [
    (_check_duplicate_ip_names, CheckStatus.OK),
    (_check_parameters_values, CheckStatus.OK),
    (_check_ext_in_to_ext_out_connections, CheckStatus.OK),
    (_check_ambigous_ports, CheckStatus.OK),

    (_check_unconnected_ports_interfaces,  CheckStatus.WARNING),
])
def test_dataflow(hdmi_specification, hdmi_dataflow, _check_function, expected_result):
    status, msg = _check_function(hdmi_dataflow, hdmi_specification)
    assert status == expected_result
