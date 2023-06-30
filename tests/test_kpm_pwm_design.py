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
def pwm_ipcores_yamls() -> list:
    return [
        'fpga_topwrap/ips/axi/axi_axil_adapter.yaml',
        'examples/pwm/ipcores/ps7.yaml',
        'examples/pwm/ipcores/litex_pwm.yml'
    ]


@pytest.fixture
def pwm_ipcores_names_to_yamls(pwm_ipcores_yamls) -> dict:
    return _ipcore_names_to_yamls_mapping(pwm_ipcores_yamls)


@pytest.fixture
def pwm_design_yaml() -> dict:
    with open('examples/pwm/project.yml', 'r') as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def pwm_specification(pwm_ipcores_yamls) -> dict:
    return ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)


@pytest.fixture
def pwm_dataflow(pwm_design_yaml, pwm_specification) -> dict:
    return kpm_dataflow_from_design_descr(pwm_design_yaml, pwm_specification)


def test_pwm_specification_generation(pwm_specification, specification_schema):
    assert len(pwm_specification['nodes']) == 5 # 3 IP cores + 2 External metanodes
    jsonschema.validate(pwm_specification, specification_schema)


class TestPWMDataflowImport:
    @pytest.fixture
    def kpm_nodes(self, pwm_design_yaml, pwm_specification):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_nodes_from_design_descr
        return [node for node in kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)]
    
    @pytest.fixture
    def kpm_metanodes(self, pwm_design_yaml):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_metanodes_from_design_descr
        return [node for node in kpm_metanodes_from_design_descr(pwm_design_yaml)]

    def test_pwm_nodes(self, kpm_nodes):
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == 3
        ps7_node = [node for node in nodes_json if node['name'] == 'ps7'][0]
        axi_node = [node for node in nodes_json if node['name']== 'axi_bridge'][0]
        pwm_node = [node for node in nodes_json if node['name'] == 'litex_pwm_top'][0]
        # check number of imported properties
        assert len(ps7_node['properties']) == 0
        assert len(axi_node['properties']) == 6
        assert len(pwm_node['properties']) == 0
        # check overrode parameter value
        axi_id_width = [prop for prop in axi_node['properties'] if prop['name'] == 'AXI_ID_WIDTH'][0]
        assert int(axi_id_width['value']) == 12
        # check number of imported interfaces
        assert len(ps7_node['interfaces']) == 5
        assert len(axi_node['interfaces']) == 4
        assert len(pwm_node['interfaces']) == 4

    def test_pwm_metanodes(self, kpm_metanodes):
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]
        assert len(metanodes_json) == 1
        assert len(metanodes_json[0]['properties']) == 0
        assert len(metanodes_json[0]['interfaces']) == 1
        assert metanodes_json[0]['interfaces'][0]['direction'] == 'input'

    def test_pwm_connections(self, pwm_design_yaml, kpm_nodes):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_connections_from_design_descr
        connections = kpm_connections_from_design_descr(pwm_design_yaml, kpm_nodes)
        assert len(connections) == 7

    def test_pwm_metanodes_connections(self, pwm_design_yaml, kpm_nodes, kpm_metanodes):
        from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_metanodes_connections_from_design_descr
        connections = kpm_metanodes_connections_from_design_descr(pwm_design_yaml, kpm_nodes, kpm_metanodes)
        assert len(connections) == 1


class TestPWMDataflowExport:
    def test_parameters(self, pwm_dataflow):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_properties_to_parameters
        axi_node = [node for node in pwm_dataflow['graph']['nodes'] if node['name'] == 'axi_bridge'][0]
        parameters = _kpm_properties_to_parameters(axi_node['properties'])
        assert parameters == {
            'ADDR_WIDTH': 32,
            'AXI_DATA_WIDTH': 32,
            'AXI_ID_WIDTH': 12,
            'AXI_STRB_WIDTH': 'AXI_DATA_WIDTH/8',
            'AXIL_DATA_WIDTH': 32,
            'AXIL_STRB_WIDTH': 'AXIL_DATA_WIDTH/8'
        }

    def test_nodes_to_ips(self, pwm_design_yaml, pwm_dataflow, pwm_ipcores_names_to_yamls):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_nodes_to_ips
        ips = _kpm_nodes_to_ips(pwm_dataflow, pwm_ipcores_names_to_yamls)
        assert ips['ips'].keys() == pwm_design_yaml['ips'].keys()

    def test_port_interfaces(self, pwm_design_yaml, pwm_dataflow, pwm_specification):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_connections_to_ports_ifaces
        connections = _kpm_connections_to_ports_ifaces(pwm_dataflow, pwm_specification)
        assert connections['ports'] == pwm_design_yaml['ports']
        assert connections['interfaces'] == pwm_design_yaml['interfaces']

    def test_externals(self, pwm_design_yaml, pwm_dataflow):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_connections_to_external
        external = _kpm_connections_to_external(pwm_dataflow)
        assert external['external']['in'] == {}
        assert external['external']['out'] == pwm_design_yaml['external']['out']
