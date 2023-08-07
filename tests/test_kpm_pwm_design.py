# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import jsonschema
import pytest
from pytest_lazy_fixtures import lf
from yaml import Loader, load

from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from fpga_topwrap.kpm_common import EXT_OUTPUT_NAME
from fpga_topwrap.kpm_dataflow_validator import (
    CheckStatus,
    _check_ambigous_ports,
    _check_duplicate_external_input_interfaces,
    _check_duplicate_external_out_inout_names,
    _check_duplicate_ip_names,
    _check_ext_in_to_ext_out_connections,
    _check_external_inputs_missing_val,
    _check_externals_metanodes_types,
    _check_parameters_values,
    _check_unconnected_ports_interfaces,
)
from fpga_topwrap.kpm_topwrap_client import _ipcore_names_to_yamls_mapping
from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

AXI_NAME = "axi_bridge"
PS7_NAME = "ps7"
PWM_NAME = "litex_pwm_top"


@pytest.fixture
def pwm_ipcores_yamls() -> list:
    return [
        "fpga_topwrap/ips/axi/axi_axil_adapter.yaml",
        "examples/pwm/ipcores/ps7.yaml",
        "examples/pwm/ipcores/litex_pwm.yml",
    ]


@pytest.fixture
def pwm_ipcores_names_to_yamls(pwm_ipcores_yamls) -> dict:
    return _ipcore_names_to_yamls_mapping(pwm_ipcores_yamls)


@pytest.fixture
def pwm_design_yaml() -> dict:
    with open("examples/pwm/project.yml", "r") as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def pwm_specification(pwm_ipcores_yamls) -> dict:
    return ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)


@pytest.fixture
def pwm_dataflow(pwm_design_yaml, pwm_specification) -> dict:
    return kpm_dataflow_from_design_descr(pwm_design_yaml, pwm_specification)


def test_pwm_specification_generation(pwm_specification, specification_schema):
    assert len(pwm_specification["nodes"]) == 6  # 3 IP cores + 3 External metanodes
    jsonschema.validate(pwm_specification, specification_schema)


class TestPWMDataflowImport:
    @pytest.fixture
    def kpm_nodes(self, pwm_design_yaml, pwm_specification):
        from fpga_topwrap.design_to_kpm_dataflow_parser import (
            kpm_nodes_from_design_descr,
        )

        return [node for node in kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)]

    @pytest.fixture
    def kpm_metanodes(self, pwm_design_yaml):
        from fpga_topwrap.design_to_kpm_dataflow_parser import (
            kpm_metanodes_from_design_descr,
        )

        return [node for node in kpm_metanodes_from_design_descr(pwm_design_yaml)]

    def test_pwm_nodes(self, kpm_nodes):
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == 3
        axi_node = next((node for node in nodes_json if node["name"] == AXI_NAME), None)
        ps7_node = next((node for node in nodes_json if node["name"] == PS7_NAME), None)
        pwm_node = next((node for node in nodes_json if node["name"] == PWM_NAME), None)
        assert None not in [axi_node, ps7_node, pwm_node]

        # check imported properties
        for prop in axi_node["properties"]:
            del prop["id"]
        assert sorted(axi_node["properties"], key=lambda prop: prop["name"]) == [
            {"name": "ADDR_WIDTH", "value": "32"},
            {"name": "AXIL_DATA_WIDTH", "value": "32"},
            {"name": "AXIL_STRB_WIDTH", "value": "AXIL_DATA_WIDTH/8"},
            {"name": "AXI_DATA_WIDTH", "value": "32"},
            {"name": "AXI_ID_WIDTH", "value": "12"},
            {"name": "AXI_STRB_WIDTH", "value": "AXI_DATA_WIDTH/8"},
        ]
        assert pwm_node["properties"] == []
        assert ps7_node["properties"] == []

        # check imported interfaces
        for prop in axi_node["interfaces"]:
            del prop["id"]
        assert sorted(axi_node["interfaces"], key=lambda iface: iface["name"]) == [
            {"name": "clk", "direction": "input", "connectionSide": "left"},
            {"name": "m_axi", "direction": "output", "connectionSide": "right"},
            {"name": "rst", "direction": "input", "connectionSide": "left"},
            {"name": "s_axi", "direction": "input", "connectionSide": "left"},
        ]

        for prop in pwm_node["interfaces"]:
            del prop["id"]
        assert sorted(pwm_node["interfaces"], key=lambda iface: iface["name"]) == [
            {"name": "pwm", "direction": "output", "connectionSide": "right"},
            {"name": "s_axi", "direction": "input", "connectionSide": "left"},
            {"name": "sys_clk", "direction": "input", "connectionSide": "left"},
            {"name": "sys_rst", "direction": "input", "connectionSide": "left"},
        ]

        for prop in ps7_node["interfaces"]:
            del prop["id"]
        assert sorted(ps7_node["interfaces"], key=lambda iface: iface["name"]) == [
            {"name": "FCLK0", "direction": "output", "connectionSide": "right"},
            {"name": "FCLK_RESET0_N", "direction": "output", "connectionSide": "right"},
            {"name": "MAXIGP0ACLK", "direction": "input", "connectionSide": "left"},
            {"name": "MAXIGP0ARESETN", "direction": "output", "connectionSide": "right"},
            {"name": "M_AXI_GP0", "direction": "output", "connectionSide": "right"},
        ]

    def test_pwm_metanodes(self, kpm_metanodes):
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]
        assert (
            len(metanodes_json) == 1
        )  # PWM design should contain only 1 `External Output` metanode

        # check the property of the `External Output` metanode
        assert len(metanodes_json[0]["properties"]) == 1
        del metanodes_json[0]["properties"][0]["id"]
        assert metanodes_json[0]["properties"][0] == {"name": "External Name", "value": "pwm"}

        # check the interface of the `External Output` metanode
        assert len(metanodes_json[0]["interfaces"]) == 1
        del metanodes_json[0]["interfaces"][0]["id"]
        assert metanodes_json[0]["interfaces"][0] == {
            "name": "external",
            "direction": "input",
            "connectionSide": "left",
        }

    def _find_node_name_by_iface_id(self, iface_id: str, nodes_json: list) -> str:
        for node in nodes_json:
            if iface_id in [iface["id"] for iface in node["interfaces"]]:
                return node["name"]

    def test_pwm_connections(self, pwm_design_yaml, kpm_nodes):
        from fpga_topwrap.design_to_kpm_dataflow_parser import (
            kpm_connections_from_design_descr,
        )

        connections_json = [
            conn.to_json_format()
            for conn in kpm_connections_from_design_descr(pwm_design_yaml, kpm_nodes)
        ]
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(connections_json) == 7

        # we have 7 ipcore<->ipcore connections, each one is represented as a pair of ids
        # let's check the number of connections for each node
        node_names = []
        for conn in connections_json:
            assert sorted(list(conn.keys())) == ["from", "id", "to"]
            node_names.append(self._find_node_name_by_iface_id(conn["from"], nodes_json))
            node_names.append(self._find_node_name_by_iface_id(conn["to"], nodes_json))
        assert node_names.count(AXI_NAME) == 4
        assert node_names.count(PS7_NAME) == 7
        assert node_names.count(PWM_NAME) == 3

    def test_pwm_metanodes_connections(self, pwm_design_yaml, kpm_nodes, kpm_metanodes):
        from fpga_topwrap.design_to_kpm_dataflow_parser import (
            kpm_metanodes_connections_from_design_descr,
        )

        connections_json = [
            conn.to_json_format()
            for conn in kpm_metanodes_connections_from_design_descr(
                pwm_design_yaml, kpm_nodes, kpm_metanodes
            )
        ]
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        metanodes_json = [metanode.to_json_format() for metanode in kpm_metanodes]
        assert len(connections_json) == 1

        assert self._find_node_name_by_iface_id(connections_json[0]["from"], nodes_json) == PWM_NAME
        assert (
            self._find_node_name_by_iface_id(connections_json[0]["to"], metanodes_json)
            == EXT_OUTPUT_NAME
        )


class TestPWMDataflowExport:
    def test_parameters(self, pwm_dataflow):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_properties_to_parameters

        axi_node = next(
            (node for node in pwm_dataflow["graph"]["nodes"] if node["name"] == AXI_NAME), None
        )
        assert axi_node is not None
        parameters = _kpm_properties_to_parameters(axi_node["properties"])
        assert parameters == {
            "ADDR_WIDTH": 32,
            "AXI_DATA_WIDTH": 32,
            "AXI_ID_WIDTH": 12,
            "AXI_STRB_WIDTH": "AXI_DATA_WIDTH/8",
            "AXIL_DATA_WIDTH": 32,
            "AXIL_STRB_WIDTH": "AXIL_DATA_WIDTH/8",
        }

    def test_nodes_to_ips(self, pwm_design_yaml, pwm_dataflow, pwm_ipcores_names_to_yamls):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_nodes_to_ips

        ips = _kpm_nodes_to_ips(pwm_dataflow, pwm_ipcores_names_to_yamls)
        assert ips.keys() == pwm_design_yaml["ips"].keys()

    def test_port_interfaces(self, pwm_dataflow, pwm_specification):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_connections_to_ports_ifaces

        connections = _kpm_connections_to_ports_ifaces(pwm_dataflow, pwm_specification)
        assert connections["ports"] == {
            PS7_NAME: {"MAXIGP0ACLK": [PS7_NAME, "FCLK0"]},
            AXI_NAME: {"clk": [PS7_NAME, "FCLK0"], "rst": [PS7_NAME, "FCLK_RESET0_N"]},
            PWM_NAME: {"sys_clk": [PS7_NAME, "FCLK0"], "sys_rst": [PS7_NAME, "FCLK_RESET0_N"]},
        }
        assert connections["interfaces"] == {
            AXI_NAME: {"s_axi": [PS7_NAME, "M_AXI_GP0"]},
            PWM_NAME: {"s_axi": [AXI_NAME, "m_axi"]},
        }

    def test_externals(self, pwm_design_yaml, pwm_dataflow, pwm_specification):
        from fpga_topwrap.kpm_dataflow_parser import _kpm_connections_to_external

        assert _kpm_connections_to_external(pwm_dataflow, pwm_specification) == {
            "ports": {PWM_NAME: {"pwm": "pwm"}},
            "interfaces": {},
            "external": {
                "ports": {"in": [], "out": ["pwm"], "inout": []},
                "interfaces": {"in": [], "out": [], "inout": []},
            },
        }


class TestPWMDataflowValidation:
    @pytest.mark.parametrize(
        "_check_function, expected_result",
        [
            (_check_duplicate_ip_names, CheckStatus.OK),
            (_check_parameters_values, CheckStatus.OK),
            (_check_ext_in_to_ext_out_connections, CheckStatus.OK),
            (_check_ambigous_ports, CheckStatus.OK),
            (_check_externals_metanodes_types, CheckStatus.OK),
            (_check_external_inputs_missing_val, CheckStatus.OK),
            (_check_duplicate_external_input_interfaces, CheckStatus.OK),
            (_check_duplicate_external_out_inout_names, CheckStatus.OK),
            (_check_unconnected_ports_interfaces, CheckStatus.WARNING),
        ],
    )
    def test_dataflow(self, pwm_specification, _check_function, pwm_dataflow, expected_result):
        status, msg = _check_function(pwm_dataflow, pwm_specification)
        assert status == expected_result
