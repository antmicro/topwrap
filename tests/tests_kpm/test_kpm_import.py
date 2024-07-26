# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.design_to_kpm_dataflow_parser import (
    kpm_connections_from_design_descr,
    kpm_constant_metanodes_from_design_descr,
    kpm_constant_metanodes_from_nodes,
    kpm_external_metanodes_from_design_descr,
    kpm_metanodes_connections_from_design_descr,
    kpm_nodes_from_design_descr,
)
from topwrap.kpm_common import EXT_OUTPUT_NAME

from .common import AXI_NAME, PS7_NAME, PWM_NAME

# PWM
PWM_IPCORE_NODES = 3  # All IP Cores from examples/pwm/project.yml

PWM_EXTERNAL_METANODES = 1  # Unique external metanodes
PWM_CONSTANT_METANODES = 0  # Unique constant metanodes
PWM_METANODES = PWM_EXTERNAL_METANODES + PWM_CONSTANT_METANODES

PWM_CORE_AXI_CONNECTIONS = 4  # Connections to AXI bridge
PWM_CORE_PS7_CONNECTIONS = 7  # Connections to PS7 module
PWM_CORE_PWM_CONNECTIONS = 3  # Connections to PWM module

# HDMI
HDMI_IPCORE_NODES = 15  # All IP Cores from examples/hdmi/project.yml

HDMI_EXTERNAL_METANODES = 29  # Unique external metanodes
HDMI_CONSTANT_METANODES = 2  # Unique constant metanodes
HDMI_METANODES = HDMI_EXTERNAL_METANODES + HDMI_CONSTANT_METANODES

HDMI_IPCORES_CONNECTIONS = 59  # Connections between IP Cores
HDMI_EXTERNAL_CONNECTIONS = 29  # Connections to external metanodes
HDMI_CONSTANT_CONNECTIONS = 8  # Connections to constant metanodes


class TestPWMDataflowImport:
    """Tests that check validity of generated PWM dataflow from design description YAML
    (i.e. PWM dataflow import feature).
    """

    def test_pwm_nodes(self, pwm_design_yaml, pwm_specification):
        """Check the validity of generated KPM nodes - test their properties values
        and interfaces names.
        """
        kpm_nodes = kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == PWM_IPCORE_NODES
        [axi_node] = list(filter(lambda node: node["instanceName"] == AXI_NAME, nodes_json))
        [ps7_node] = list(filter(lambda node: node["instanceName"] == PS7_NAME, nodes_json))
        [pwm_node] = list(filter(lambda node: node["instanceName"] == PWM_NAME, nodes_json))

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

    def test_pwm_metanodes(self, pwm_design_yaml, pwm_specification):
        """Check the number of generated metanodes and their contents. External metanodes should
        always contain one "External Name" property and one "external" interface.
        """
        kpm_ext_metanodes = kpm_external_metanodes_from_design_descr(pwm_design_yaml)
        kpm_const_metanodes = kpm_constant_metanodes_from_design_descr(
            pwm_design_yaml, pwm_specification
        )
        kpm_metanodes = kpm_ext_metanodes + kpm_const_metanodes

        ext_metanodes_json = [node.to_json_format() for node in kpm_ext_metanodes]
        const_metanodes_json = [node.to_json_format() for node in kpm_const_metanodes]
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]
        # PWM design should contain only 1 `External Output` metanode
        assert len(ext_metanodes_json) == PWM_EXTERNAL_METANODES
        assert len(const_metanodes_json) == PWM_CONSTANT_METANODES
        assert len(metanodes_json) == PWM_METANODES

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
                return node["instanceName"]

    def test_pwm_connections(self, pwm_design_yaml, pwm_specification):
        """Check the number of generated connections between two nodes representing IP cores
        (i.e. `ipcore_1`<->`ipcore_2` connections).
        """
        kpm_nodes = kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)
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
        assert node_names.count(AXI_NAME) == PWM_CORE_AXI_CONNECTIONS
        assert node_names.count(PS7_NAME) == PWM_CORE_PS7_CONNECTIONS
        assert node_names.count(PWM_NAME) == PWM_CORE_PWM_CONNECTIONS

    def test_pwm_metanodes_connections(self, pwm_design_yaml, pwm_specification):
        """Check the number of generated connections between a node representing IP core and
        an metanode (i.e. `ipcore`<->`metanode` connections).
        """
        kpm_nodes = kpm_nodes_from_design_descr(pwm_design_yaml, pwm_specification)
        kpm_metanodes = kpm_external_metanodes_from_design_descr(pwm_design_yaml)

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
    def test_hdmi_nodes(self, hdmi_design_yaml, hdmi_specification):
        """Check the validity of generated KPM nodes - test some of their properties values."""
        kpm_nodes = kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)
        nodes_json = [node.to_json_format() for node in kpm_nodes]
        assert len(nodes_json) == HDMI_IPCORE_NODES
        # check overrode {'value': ..., 'width': ...} parameter value
        [axi_interconnect_node] = list(
            filter(lambda node: node["instanceName"] == "axi_interconnect0", nodes_json)
        )
        [m_addr_width] = list(
            filter(lambda prop: prop["name"] == "M_ADDR_WIDTH", axi_interconnect_node["properties"])
        )
        assert m_addr_width["value"] == "96'h100000001000000010"

    def test_hdmi_metanodes(self, hdmi_design_yaml, hdmi_specification):
        """Check the number of generated external and constant metanodes."""
        kpm_ext_metanodes = kpm_external_metanodes_from_design_descr(hdmi_design_yaml)
        kpm_const_metanodes = kpm_constant_metanodes_from_design_descr(
            hdmi_design_yaml, hdmi_specification
        )
        kpm_metanodes = kpm_ext_metanodes + kpm_const_metanodes

        ext_metanodes_json = [node.to_json_format() for node in kpm_ext_metanodes]
        const_metanodes_json = [node.to_json_format() for node in kpm_const_metanodes]
        metanodes_json = [node.to_json_format() for node in kpm_metanodes]

        assert len(ext_metanodes_json) == HDMI_EXTERNAL_METANODES
        assert len(const_metanodes_json) == HDMI_CONSTANT_METANODES
        assert len(metanodes_json) == HDMI_METANODES

    def test_hdmi_connections(self, hdmi_design_yaml, hdmi_specification):
        """Check the number of generated connections between nodes representing IP cores
        (i.e. `ipcore_1`<->`ipcore_2` connections).
        """
        kpm_nodes = kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)
        connections = kpm_connections_from_design_descr(hdmi_design_yaml, kpm_nodes)
        assert len(connections) == HDMI_IPCORES_CONNECTIONS

    def test_hdmi_metanodes_connections(self, hdmi_design_yaml, hdmi_specification):
        """Check the number of generated connections between a node representing IP core and
        a metanode (i.e. `ipcore`<->`metanode` connections).
        """
        kpm_nodes = kpm_nodes_from_design_descr(hdmi_design_yaml, hdmi_specification)
        ext_metanodes = kpm_external_metanodes_from_design_descr(hdmi_design_yaml)
        const_metanodes = kpm_constant_metanodes_from_nodes(kpm_nodes)

        ext_metanodes_connections = kpm_metanodes_connections_from_design_descr(
            hdmi_design_yaml, kpm_nodes, ext_metanodes
        )
        const_metanodes_connections = kpm_metanodes_connections_from_design_descr(
            hdmi_design_yaml, kpm_nodes, const_metanodes
        )

        assert len(ext_metanodes_connections) == HDMI_EXTERNAL_CONNECTIONS
        assert len(const_metanodes_connections) == HDMI_CONSTANT_CONNECTIONS
