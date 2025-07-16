# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from topwrap.backend.kpm.dataflow import KpmDataflowBackend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.model.module import Module
from topwrap.util import JsonType, read_json_file


@pytest.fixture
def test_dirs() -> Dict[str, Path]:
    COMMON = "tests/data/data_kpm/"
    paths = {}
    for glob in (COMMON + "examples/*", COMMON + "conversions/*"):
        for path in Path(".").glob(glob):
            ip_name = path.stem
            paths[ip_name] = path
    return paths


@pytest.fixture
def all_specification_files(test_dirs: Dict[str, Path]) -> Dict[str, JsonType]:
    return {
        ip_name: read_json_file(dir / f"specification_{ip_name}.json")
        for ip_name, dir in test_dirs.items()
    }


@pytest.fixture
def all_design_paths(test_dirs: Dict[str, Path]) -> Dict[str, Path]:
    data = {}
    for ip_name, dir in test_dirs.items():
        if dir.parts[-2] == "examples":
            data[ip_name] = Path("examples") / ip_name / "project.yaml"
        else:
            data[ip_name] = dir / f"project_{ip_name}.yaml"

    return data


@pytest.fixture
def all_design_modules(all_design_paths: Dict[str, Path]) -> Dict[str, Module]:
    frontend = YamlFrontend()
    return {name: next(frontend.parse_files([path])) for name, path in all_design_paths.items()}


def _filter_id(object: Dict[Any, Any]):
    return {name: value for name, value in object.items() if name != "id"}


def _find_node_name_by_iface_id(iface_id: str, nodes: list[JsonType]) -> Optional[str]:
    for node in nodes:
        if iface_id in [iface["id"] for iface in node["interfaces"]]:
            return node["instanceName"]


def _find_node_kind(node: JsonType, spec: JsonType) -> Optional[str]:
    name = node["name"]
    for node_spec in spec["nodes"]:
        if name == node_spec["name"]:
            return node_spec["category"]


# Common node names
AXI_NAME = "axi_bridge"
PS7_NAME = "ps7"
PWM_NAME = "litex_pwm_top"

# PWM
PWM_IPCORE_NODES = 3  # All IP Cores from examples/pwm/project.yaml

PWM_EXTERNAL_METANODES = 1  # Unique external metanodes
PWM_CONSTANT_METANODES = 0  # Unique constant metanodes
PWM_METANODES = 1 + PWM_EXTERNAL_METANODES + PWM_CONSTANT_METANODES  # Identifier + others

PWM_CORE_AXI_CONNECTIONS = 4  # Connections to AXI bridge
PWM_CORE_PS7_CONNECTIONS = 7  # Connections to PS7 module
PWM_CORE_PWM_CONNECTIONS = 4  # Connections to PWM module

PWM_UNIQUE_CONNECTIONS = 8  # Total unique connections

# HDMI
HDMI_IPCORE_NODES = 15  # All IP Cores from examples/hdmi/project.yaml

HDMI_EXTERNAL_METANODES = 29  # Unique external metanodes
HDMI_CONSTANT_METANODES = 2  # Unique constant metanodes
HDMI_METANODES = 1 + HDMI_EXTERNAL_METANODES + HDMI_CONSTANT_METANODES  # Identifier + others

HDMI_UNIQUE_CONNECTIONS = 96  # Total unique connections

# HIERARCHY
HIERARCHY_GRAPHS = 5  # 5 graphs in total (main + 4 sub)

HIERARCHY_IPCORE_NODES = 8
HIERARCHY_SUBGRAPH_NODES = 4

HIERARCHY_EXTERNAL_METANODES = 18
HIERARCHY_CONSTANT_METANODES = 2
# Identifier per subgraph + others
HIERARCHY_METANODES = HIERARCHY_GRAPHS + HIERARCHY_EXTERNAL_METANODES + HIERARCHY_CONSTANT_METANODES

HIERARCHY_CONNECTIONS = 26


class TestKpmBackendPWMExample:
    @pytest.fixture
    def pwm_specification(self, all_specification_files: Dict[str, JsonType]) -> JsonType:
        return all_specification_files["pwm"]

    @pytest.fixture
    def pwm_module(self, all_design_modules: Dict[str, Module]) -> Module:
        return all_design_modules["pwm"]

    @pytest.fixture
    def pwm_dataflow(self, pwm_module: Module, pwm_specification: JsonType) -> JsonType:
        assert pwm_module.design

        flow = KpmDataflowBackend(pwm_specification)
        flow.represent_design(pwm_module.design)
        return flow.build()

    def test_elements(self, pwm_dataflow: JsonType):
        """
        Check whether the dataflow contains the expected elements.
        """

        assert "graphs" in pwm_dataflow
        assert len(pwm_dataflow["graphs"]) == 1

        graph = pwm_dataflow["graphs"][0]
        assert "nodes" in graph
        assert "connections" in graph

        assert len(graph["nodes"]) == PWM_IPCORE_NODES + PWM_METANODES

    def test_nodes(self, pwm_dataflow: JsonType):
        """
        Check some the generated nodes, their properties, and their interfaces.
        """

        graph = pwm_dataflow["graphs"][0]
        nodes = graph["nodes"]

        [axi_node] = list(filter(lambda node: node["instanceName"] == AXI_NAME, nodes))
        [ps7_node] = list(filter(lambda node: node["instanceName"] == PS7_NAME, nodes))
        [pwm_node] = list(filter(lambda node: node["instanceName"] == PWM_NAME, nodes))

        axi_props = [_filter_id(x) for x in axi_node["properties"]]
        assert sorted(axi_props, key=lambda prop: prop["name"]) == [
            {"name": "ADDR_WIDTH", "value": "32"},
            {"name": "AXIL_DATA_WIDTH", "value": "32"},
            {"name": "AXIL_STRB_WIDTH", "value": "AXIL_DATA_WIDTH/8"},
            {"name": "AXI_DATA_WIDTH", "value": "32"},
            {"name": "AXI_ID_WIDTH", "value": "12"},
            {"name": "AXI_STRB_WIDTH", "value": "AXI_DATA_WIDTH/8"},
        ]
        assert pwm_node["properties"] == []
        assert ps7_node["properties"] == []

        axi_ifs = [_filter_id(x) for x in axi_node["interfaces"]]
        assert sorted(axi_ifs, key=lambda iface: iface["name"]) == [
            {"name": "clk", "direction": "input", "side": "left"},
            {"name": "m_axi", "direction": "output", "side": "right"},
            {"name": "rst", "direction": "input", "side": "left"},
            {"name": "s_axi", "direction": "input", "side": "left"},
        ]

        pwm_ifs = [_filter_id(x) for x in pwm_node["interfaces"]]
        assert sorted(pwm_ifs, key=lambda iface: iface["name"]) == [
            {"name": "pwm", "direction": "output", "side": "right"},
            {"name": "s_axi", "direction": "input", "side": "left"},
            {"name": "sys_clk", "direction": "input", "side": "left"},
            {"name": "sys_rst", "direction": "input", "side": "left"},
        ]

        ps7_ifs = [_filter_id(x) for x in ps7_node["interfaces"]]
        assert sorted(ps7_ifs, key=lambda iface: iface["name"]) == [
            {"name": "FCLK0", "direction": "output", "side": "right"},
            {"name": "FCLK_RESET0_N", "direction": "output", "side": "right"},
            {"name": "MAXIGP0ACLK", "direction": "input", "side": "left"},
            {"name": "MAXIGP0ARESETN", "direction": "output", "side": "right"},
            {"name": "M_AXI_GP0", "direction": "output", "side": "right"},
        ]

    def test_connections(self, pwm_dataflow: JsonType):
        """
        Check the number of connection between nodes.
        """

        graph = pwm_dataflow["graphs"][0]
        nodes = graph["nodes"]
        connections = graph["connections"]

        assert len(connections) == PWM_UNIQUE_CONNECTIONS

        node_names = []

        for conn in connections:
            assert sorted(list(conn.keys())) == ["from", "id", "to"]
            node_names.append(_find_node_name_by_iface_id(conn["from"], nodes))
            node_names.append(_find_node_name_by_iface_id(conn["to"], nodes))
        assert node_names.count(AXI_NAME) == PWM_CORE_AXI_CONNECTIONS
        assert node_names.count(PS7_NAME) == PWM_CORE_PS7_CONNECTIONS
        assert node_names.count(PWM_NAME) == PWM_CORE_PWM_CONNECTIONS

    def test_metanodes(self, pwm_dataflow: JsonType, pwm_specification: JsonType):
        """
        Check the generated metanodes.
        """

        graph = pwm_dataflow["graphs"][0]
        nodes = graph["nodes"]

        metanodes = {
            node["instanceName"]: node
            for node in nodes
            if _find_node_kind(node, pwm_specification) == "Metanode"
        }

        assert len(metanodes) == PWM_METANODES
        assert metanodes["Identifier"]["name"] == "Identifier"
        assert metanodes["pwm"]["name"] == "External I/O"

        id_props = [_filter_id(x) for x in metanodes["Identifier"]["properties"]]
        assert sorted(id_props, key=lambda prop: prop["name"]) == [
            {"name": "Library", "value": "libdefault"},
            {"name": "Name", "value": "top"},
            {"name": "Vendor", "value": "vendor"},
        ]

        pwm_ifs = [_filter_id(x) for x in metanodes["pwm"]["interfaces"]]
        assert sorted(pwm_ifs, key=lambda iface: iface["name"]) == [
            {"name": "in", "direction": "input"},
            {"name": "inout", "direction": "inout"},
            {"name": "out", "direction": "output", "externalName": "pwm"},
        ]


class TestKpmBackendHDMIExample:
    @pytest.fixture
    def hdmi_specification(self, all_specification_files: Dict[str, JsonType]) -> JsonType:
        return all_specification_files["hdmi"]

    @pytest.fixture
    def hdmi_module(self, all_design_modules: Dict[str, Module]) -> Module:
        return all_design_modules["hdmi"]

    @pytest.fixture
    def hdmi_dataflow(self, hdmi_module: Module, hdmi_specification: JsonType) -> JsonType:
        assert hdmi_module.design

        flow = KpmDataflowBackend(hdmi_specification)
        flow.represent_design(hdmi_module.design)
        return flow.build()

    def test_elements(self, hdmi_dataflow: JsonType):
        """
        Check whether the dataflow contains the expected elements.
        """

        assert "graphs" in hdmi_dataflow
        assert len(hdmi_dataflow["graphs"]) == 1

        graph = hdmi_dataflow["graphs"][0]
        assert "nodes" in graph
        assert "connections" in graph

        assert len(graph["nodes"]) == HDMI_IPCORE_NODES + HDMI_METANODES

    def test_nodes(self, hdmi_dataflow: JsonType):
        """
        Check some the generated nodes, their properties, and their interfaces.
        """

        graph = hdmi_dataflow["graphs"][0]
        nodes = graph["nodes"]

        [axi_node] = list(filter(lambda node: node["instanceName"] == "axi_interconnect0", nodes))
        [conv_node] = list(
            filter(lambda node: node["instanceName"] == "axi_protocol_converter0", nodes)
        )

        axi_props = [_filter_id(x) for x in axi_node["properties"]]
        want_axi_props = [
            {"name": "M_ADDR_WIDTH", "value": "96'd295147905248072302608"},
            {"name": "STRB_WIDTH", "value": "DATA_WIDTH/8"},
            {"name": "M_BASE_ADDR", "value": "118'd20970027271917541136636313600"},
        ]
        assert all(x in axi_props for x in want_axi_props)
        assert conv_node["properties"] == []

        conv_ifs = [_filter_id(x) for x in conv_node["interfaces"]]
        assert sorted(conv_ifs, key=lambda iface: iface["name"]) == [
            {"name": "M_AXI", "direction": "output", "side": "right"},
            {"name": "S_AXI", "direction": "input", "side": "left"},
            {"name": "aclk", "direction": "input", "side": "left"},
            {"name": "aresetn", "direction": "input", "side": "left"},
        ]

    def test_connections(self, hdmi_dataflow: JsonType):
        """
        Check the number of connection between nodes.
        """

        graph = hdmi_dataflow["graphs"][0]
        connections = graph["connections"]

        assert len(connections) == HDMI_UNIQUE_CONNECTIONS

    def test_metanodes(self, hdmi_dataflow: JsonType, hdmi_specification: JsonType):
        """
        Check some of the generated metanodes.
        """

        graph = hdmi_dataflow["graphs"][0]
        nodes = graph["nodes"]

        metanodes = {
            node["instanceName"]: node
            for node in nodes
            if _find_node_kind(node, hdmi_specification) == "Metanode"
        }

        assert (
            sum(1 for node in nodes if _find_node_kind(node, hdmi_specification) == "Metanode")
            == HDMI_METANODES
        )
        assert metanodes["Identifier"]["name"] == "Identifier"
        assert metanodes["HDMI_D0_P"]["name"] == "External I/O"
        assert metanodes["HDMI_D0_N"]["name"] == "External I/O"

        id_props = [_filter_id(x) for x in metanodes["Identifier"]["properties"]]
        assert sorted(id_props, key=lambda prop: prop["name"]) == [
            {"name": "Library", "value": "libdefault"},
            {"name": "Name", "value": "top"},
            {"name": "Vendor", "value": "vendor"},
        ]

        d0_p_ifs = [_filter_id(x) for x in metanodes["HDMI_D0_P"]["interfaces"]]
        assert sorted(d0_p_ifs, key=lambda iface: iface["name"]) == [
            {"name": "in", "direction": "input"},
            {"name": "inout", "direction": "inout"},
            {"name": "out", "direction": "output", "externalName": "HDMI_D0_P"},
        ]


class TestKpmBackendHierarchyExample:
    @pytest.fixture
    def hierarchy_specification(self, all_specification_files: Dict[str, JsonType]) -> JsonType:
        return all_specification_files["hierarchy"]

    @pytest.fixture
    def hierarchy_module(self, all_design_modules: Dict[str, Module]) -> Module:
        return all_design_modules["hierarchy"]

    @pytest.fixture
    def hierarchy_dataflow(
        self, hierarchy_module: Module, hierarchy_specification: JsonType
    ) -> JsonType:
        assert hierarchy_module.design

        flow = KpmDataflowBackend(hierarchy_specification)
        flow.represent_design(hierarchy_module.design, depth=-1)
        return flow.build()

    @pytest.fixture
    def all_nodes(self, hierarchy_dataflow: JsonType) -> list[JsonType]:
        nodes = []
        for graph in hierarchy_dataflow["graphs"]:
            nodes += graph["nodes"]
        return nodes

    @pytest.fixture
    def all_connections(self, hierarchy_dataflow: JsonType) -> list[JsonType]:
        connections = []
        for graph in hierarchy_dataflow["graphs"]:
            connections += graph["connections"]
        return connections

    def test_elements(self, hierarchy_dataflow: JsonType, all_nodes: list[JsonType]):
        """
        Check whether the dataflow contains the expected elements.
        """

        assert "graphs" in hierarchy_dataflow
        assert len(hierarchy_dataflow["graphs"]) == 5

        for graph in hierarchy_dataflow["graphs"]:
            assert "nodes" in graph
            assert "connections" in graph

        assert (
            len(all_nodes)
            == HIERARCHY_IPCORE_NODES + HIERARCHY_SUBGRAPH_NODES + HIERARCHY_METANODES
        )

    def test_nodes(self, all_nodes: list[JsonType]):
        """
        Check some the generated nodes, their properties, and their interfaces.
        """

        [c_mod_1] = list(filter(lambda node: node["instanceName"] == "c_mod_1", all_nodes))
        [s1_mod_2] = list(filter(lambda node: node["instanceName"] == "s1_mod_2", all_nodes))

        [max_value] = list(filter(lambda prop: prop["name"] == "MAX_VALUE", c_mod_1["properties"]))
        assert max_value["value"] == "16"
        assert s1_mod_2["properties"] == []

        # check interfaces on nodes that are on different depths
        c_mod_1_ifs = [_filter_id(x) for x in c_mod_1["interfaces"]]
        assert sorted(c_mod_1_ifs, key=lambda iface: iface["name"]) == [
            {"direction": "output", "name": "c_int_out_1", "side": "right"},
            {"direction": "input", "name": "c_mod_in_1", "side": "left"},
        ]

        s1_mod_2_ifs = [_filter_id(x) for x in s1_mod_2["interfaces"]]
        assert sorted(s1_mod_2_ifs, key=lambda iface: iface["name"]) == [
            {"direction": "output", "name": "cs_s1_f_int_out_1", "side": "right"},
            {"direction": "input", "name": "cs_s1_mint_in_1", "side": "left"},
        ]

    def test_connections(self, all_nodes: list[JsonType], all_connections: list[JsonType]):
        """
        Check the number of connection between nodes.
        """

        assert len(all_connections) == HIERARCHY_CONNECTIONS

        node_names = []
        for conn in all_connections:
            node_names.append(_find_node_name_by_iface_id(conn["to"], all_nodes))
            node_names.append(_find_node_name_by_iface_id(conn["from"], all_nodes))
        conn_dict = {item: node_names.count(item) for item in node_names}
        want_conn_dict = {
            "Constant": 2,
            "ex_in_1": 1,
            "ex_out_1": 1,
            "ex_out_2": 1,
            "c_mod_1": 2,
            "c_mod_2": 2,
            "c_mod_3": 4,
            "complex_sub": 2,
            "cs_in_1": 1,
            "cs_out_1": 1,
            "counter": 3,
            "c_in_1": 1,
            "c_in_2": 1,
            "c_out_1": 1,
            "s1_mod_1": 4,
            "s1_mod_2": 2,
            "s1_mod_3": 2,
            "s2_mod_1": 4,
            "s2_mod_2": 3,
            "sub_1": 4,
            "cs_s1_int_const_in": 1,
            "cs_s1_int_out_1": 1,
            "cs_s1_int_out_2": 1,
            "cs_s1_mod_in_1": 1,
            "sub_2": 3,
            "cs_s2_int_in_1": 1,
            "cs_s2_int_in_2": 1,
            "cs_s2_mod_out_1": 1,
        }

        assert conn_dict == want_conn_dict

    def test_metanodes(self, all_nodes: list[JsonType], hierarchy_specification: JsonType):
        """
        Check number of generated metanodes.
        """

        assert (
            sum(
                1
                for node in all_nodes
                if _find_node_kind(node, hierarchy_specification) == "Metanode"
            )
            == HIERARCHY_METANODES
        )

    def test_subgraph_nodes(self, all_nodes: list[JsonType]):
        """
        Check generated subgraph nodes.
        """

        subgraph_nodes = [node for node in all_nodes if "subgraph" in node]

        assert len(subgraph_nodes) == HIERARCHY_SUBGRAPH_NODES

        [counter] = list(filter(lambda node: node["instanceName"] == "counter", subgraph_nodes))
        [complex_sub] = list(
            filter(lambda node: node["instanceName"] == "complex_sub", subgraph_nodes)
        )
        [sub_2] = list(filter(lambda node: node["instanceName"] == "sub_2", subgraph_nodes))

        counter_ifs = [_filter_id(x) for x in counter["interfaces"]]
        assert sorted(counter_ifs, key=lambda iface: iface["name"]) == [
            {"direction": "input", "name": "c_in_1", "side": "left"},
            {"direction": "input", "name": "c_in_2", "side": "left"},
            {"direction": "output", "name": "c_out_1", "side": "right"},
        ]

        complex_sub_ifs = [_filter_id(x) for x in complex_sub["interfaces"]]
        assert sorted(complex_sub_ifs, key=lambda iface: iface["name"]) == [
            {"direction": "input", "name": "cs_empty_port_in", "side": "left"},
            {"direction": "input", "name": "cs_in_1", "side": "left"},
            {"direction": "output", "name": "cs_out_1", "side": "right"},
        ]

        sub_2_ifs = [_filter_id(x) for x in sub_2["interfaces"]]
        assert sorted(sub_2_ifs, key=lambda iface: iface["name"]) == [
            {"direction": "input", "name": "cs_s2_int_in_1", "side": "left"},
            {"direction": "input", "name": "cs_s2_int_in_2", "side": "left"},
            {"direction": "output", "name": "cs_s2_mod_out_1", "side": "right"},
        ]
