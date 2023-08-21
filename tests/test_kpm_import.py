# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

from fpga_topwrap.design_to_kpm_dataflow_parser import (
    kpm_connections_from_design_descr,
    kpm_metanodes_connections_from_design_descr,
    kpm_metanodes_from_design_descr,
    kpm_nodes_from_design_descr,
)
from fpga_topwrap.kpm_common import EXT_OUTPUT_NAME
from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

AXI_NAME = "axi_bridge"
PS7_NAME = "ps7"
PWM_NAME = "litex_pwm_top"


class TestPWMDataflowImport:
    def test_pwm_nodes(self, pwm_design_yaml, pwm_ipcores_yamls):
        pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
        kpm_nodes = [
            node for node in kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)
        ]
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == 3
        [axi_node] = list(filter(lambda node: node["name"] == AXI_NAME, nodes_json))
        [ps7_node] = list(filter(lambda node: node["name"] == PS7_NAME, nodes_json))
        [pwm_node] = list(filter(lambda node: node["name"] == PWM_NAME, nodes_json))

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

    def test_pwm_metanodes(self, pwm_design_yaml):
        kpm_metanodes = [node for node in kpm_metanodes_from_design_descr(pwm_design_yaml)]
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]
        # PWM design should contain only 1 `External Output` metanode
        assert len(metanodes_json) == 1

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

    def test_pwm_connections(self, pwm_design_yaml, pwm_ipcores_yamls):
        pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
        kpm_nodes = [
            node for node in kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)
        ]
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

    def test_pwm_metanodes_connections(self, pwm_design_yaml, pwm_ipcores_yamls):
        pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
        kpm_nodes = [
            node for node in kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)
        ]
        kpm_metanodes = [node for node in kpm_metanodes_from_design_descr(pwm_design_yaml)]
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


class TestHDMIDataflowImport:
    def test_hdmi_nodes(self, hdmi_design_yaml, hdmi_ipcores_yamls):
        hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
        kpm_nodes = [
            node for node in kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)
        ]
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == 15
        # check overrode {'value': ..., 'width': ...} parameter value
        axi_interconnect_node = [
            node for node in nodes_json if node["name"] == "axi_interconnect0"
        ][0]
        m_addr_width = [
            prop for prop in axi_interconnect_node["properties"] if prop["name"] == "M_ADDR_WIDTH"
        ][0]
        assert m_addr_width["value"] == "96'h100000001000000010"

    def test_hdmi_metanodes(self, hdmi_design_yaml):
        kpm_metanodes = [node for node in kpm_metanodes_from_design_descr(hdmi_design_yaml)]
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]
        assert len(metanodes_json) == 8

    def test_hdmi_connections(self, hdmi_design_yaml, hdmi_ipcores_yamls):
        hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
        kpm_nodes = [
            node for node in kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)
        ]
        connections = kpm_connections_from_design_descr(hdmi_design_yaml, kpm_nodes)
        assert len(connections) == 59

    def test_hdmi_metanodes_connections(self, hdmi_design_yaml, hdmi_ipcores_yamls):
        hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
        kpm_nodes = [
            node for node in kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)
        ]
        kpm_metanodes = [node for node in kpm_metanodes_from_design_descr(hdmi_design_yaml)]

        connections = kpm_metanodes_connections_from_design_descr(
            hdmi_design_yaml, kpm_nodes, kpm_metanodes
        )
        assert len(connections) == 8
