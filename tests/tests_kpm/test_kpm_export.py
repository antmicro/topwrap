# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

import pytest
from deepdiff import DeepDiff

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import KPMDataflowExternalMetanode
from topwrap.kpm_common import (
    EXT_INOUT_NAME,
    get_all_graph_nodes,
    get_entry_graph,
    graph_to_isolated_dataflow,
    is_subgraph_node,
)
from topwrap.kpm_dataflow_parser import (
    KPMExportException,
    _kpm_connections_to_constant,
    _kpm_gather_all_graph_externals,
    _kpm_nodes_to_ips,
    _kpm_parse_connections_between_nodes,
    _kpm_properties_to_parameters,
    kpm_dataflow_to_design,
)
from topwrap.util import JsonType, UnreachableError

from .common import AXI_NAME, PS7_NAME, PWM_NAME
from .test_kpm_validation import get_dataflow_test


class TestPWMDataflowExport:
    """Tests that check validity of generated design description YAML from PWM dataflow
    (i.e. PWM dataflow export feature).
    """

    def test_parameters(self, pwm_dataflow):
        """Check whether generated parameters values match the overridden values from
        `examples/pwm/project.yaml` and default values from IP core description YAMLs.
        """
        [axi_node] = list(
            filter(
                lambda node: node["instanceName"] == AXI_NAME,
                get_all_graph_nodes(pwm_dataflow),
            )
        )
        parameters = _kpm_properties_to_parameters(axi_node["properties"])
        assert parameters == {
            "ADDR_WIDTH": 32,
            "AXI_DATA_WIDTH": 32,
            "AXI_ID_WIDTH": 12,
            "AXI_STRB_WIDTH": "AXI_DATA_WIDTH/8",
            "AXIL_DATA_WIDTH": 32,
            "AXIL_STRB_WIDTH": "AXIL_DATA_WIDTH/8",
        }

    def test_nodes_to_ips(self, pwm_design: DesignDescription, pwm_dataflow, pwm_specification):
        """Check whether generated IP cores names in "ips" section of a design description YAML
        match the values from `examples/pwm/project.yaml`.
        """

        ips = _kpm_nodes_to_ips(pwm_dataflow, pwm_specification)
        assert ips.keys() == pwm_design.ips.keys()

    def test_port_interfaces(self, pwm_dataflow, pwm_specification):
        """Check whether generated connection descriptions in "ports" and "interfaces" sections
        of a design description YAML match the values from `examples/pwm/project.yaml`.
        """
        connections = _kpm_parse_connections_between_nodes(pwm_dataflow, pwm_specification)
        assert connections.ports == {
            PS7_NAME: {"MAXIGP0ACLK": (PS7_NAME, "FCLK0")},
            AXI_NAME: {"clk": (PS7_NAME, "FCLK0"), "rst": (PS7_NAME, "FCLK_RESET0_N")},
            PWM_NAME: {"sys_clk": (PS7_NAME, "FCLK0"), "sys_rst": (PS7_NAME, "FCLK_RESET0_N")},
        }
        assert connections.interfaces == {
            AXI_NAME: {"s_axi": (PS7_NAME, "M_AXI_GP0")},
            PWM_NAME: {"s_axi": (AXI_NAME, "m_axi")},
        }

    def test_externals(self, pwm_dataflow, pwm_specification):
        """Check whether generated external ports/interfaces descriptions in "externals" section
        of a design description YAML match the values from `examples/pwm/project.yaml`.
        """
        assert (
            DeepDiff(
                _kpm_gather_all_graph_externals(pwm_dataflow, pwm_specification).to_dict(),
                {
                    "ports": {PWM_NAME: {"pwm": "pwm"}},
                    "external": {
                        "ports": {"out": ["pwm"]},
                    },
                },
            )
            == {}
        )

    def test_constants(self, pwm_dataflow):
        """Check whether generated constant ports descriptions match the values
        from `examples/pwm/project.yaml`.
        """
        assert _kpm_connections_to_constant(pwm_dataflow).to_dict() == {}


class TestHDMIDataflowExport:
    """Tests that check validity of generated design description YAML from HDMI dataflow
    (i.e. HDMI dataflow export feature).
    """

    def test_parameters(self, hdmi_dataflow):
        """Check whether some generated parameters values match the values from
        `examples/hdmi/project.yaml`.
        """
        [axi_node] = list(
            filter(
                lambda node: node["instanceName"] == "axi_interconnect0",
                get_all_graph_nodes(hdmi_dataflow),
            )
        )
        parameters = _kpm_properties_to_parameters(axi_node["properties"])
        assert parameters["ADDR_WIDTH"] == 32
        assert parameters["M_ADDR_WIDTH"] == {"value": int("0x100000001000000010", 16), "width": 96}

    def test_nodes_to_ips(self, hdmi_design: DesignDescription, hdmi_dataflow, hdmi_specification):
        """Check whether generated IP cores names in "ips" section of a design description YAML
        match the values from `examples/hdmi/project.yaml`.
        """
        ips = _kpm_nodes_to_ips(hdmi_dataflow, hdmi_specification)
        assert ips.keys() == hdmi_design.ips.keys()

    def test_interfaces(self, hdmi_design: DesignDescription, hdmi_dataflow, hdmi_specification):
        """Check whether generated connection descriptions in "interfaces" sections
        of a design description YAML match the values from `examples/hdmi/project.yaml`.

        For now we don't test validity of "ports" section, since in `examples/pwm/project.yaml`
        some ports are driven by constants. This feature is not yet supported in KPM.
        """
        connections = _kpm_parse_connections_between_nodes(hdmi_dataflow, hdmi_specification)
        assert connections.interfaces == hdmi_design.design.interfaces

    def test_externals(self, hdmi_dataflow, hdmi_specification):
        """Check whether generated external ports/interfaces descriptions in "externals" section
        of a design description YAML match the values from `examples/hdmi/project.yaml`.
        """

        current_external_conn = _kpm_gather_all_graph_externals(
            hdmi_dataflow, hdmi_specification
        ).to_dict()
        expected_external_conn = {
            "ports": {
                "hdmi": {
                    "HDMI_CLK_P": "HDMI_CLK_P",
                    "HDMI_CLK_N": "HDMI_CLK_N",
                    "HDMI_D0_P": "HDMI_D0_P",
                    "HDMI_D0_N": "HDMI_D0_N",
                    "HDMI_D1_P": "HDMI_D1_P",
                    "HDMI_D1_N": "HDMI_D1_N",
                    "HDMI_D2_P": "HDMI_D2_P",
                    "HDMI_D2_N": "HDMI_D2_N",
                }
            },
            "external": {
                "ports": {
                    "out": [
                        "HDMI_CLK_P",
                        "HDMI_CLK_N",
                        "HDMI_D0_P",
                        "HDMI_D0_N",
                        "HDMI_D1_P",
                        "HDMI_D1_N",
                        "HDMI_D2_P",
                        "HDMI_D2_N",
                    ],
                    "inout": [
                        ("ps7", "ddr_addr"),
                        ("ps7", "ddr_bankaddr"),
                        ("ps7", "ddr_cas_n"),
                        ("ps7", "ddr_cke"),
                        ("ps7", "ddr_clk"),
                        ("ps7", "ddr_clk_n"),
                        ("ps7", "ddr_cs_n"),
                        ("ps7", "ddr_dm"),
                        ("ps7", "ddr_dq"),
                        ("ps7", "ddr_dqs"),
                        ("ps7", "ddr_dqs_n"),
                        ("ps7", "ddr_drstb"),
                        ("ps7", "ddr_odt"),
                        ("ps7", "ddr_ras_n"),
                        ("ps7", "ddr_vr_n"),
                        ("ps7", "ddr_vr"),
                        ("ps7", "ddr_web"),
                        ("ps7", "ps_mio"),
                        ("ps7", "ps_clk"),
                        ("ps7", "ps_porb"),
                        ("ps7", "ps_srstb"),
                    ],
                }
            },
        }
        difference = DeepDiff(current_external_conn, expected_external_conn, ignore_order=True)
        assert difference == {}

    def test_constants(self, hdmi_dataflow):
        """Check whether generated constant ports description match the values
        from `examples/hdmi/project.yaml`.
        """
        assert _kpm_connections_to_constant(hdmi_dataflow).to_dict() == {
            "ports": {
                "reset0": {
                    "aux_reset_in": 0,
                    "dcm_locked": 1,
                    "ext_reset_in": 0,
                    "mb_debug_sys_rst": 0,
                },
                "reset1": {
                    "aux_reset_in": 0,
                    "dcm_locked": 1,
                    "ext_reset_in": 0,
                    "mb_debug_sys_rst": 0,
                },
            }
        }


class TestHierarchyDataflowExport:
    def test_parameters(self, hierarchy_dataflow):
        [c_mod_1] = list(
            filter(
                lambda node: node["instanceName"] == "c_mod_1",
                get_all_graph_nodes(hierarchy_dataflow),
            )
        )
        parameters = _kpm_properties_to_parameters(c_mod_1["properties"])
        assert parameters["MAX_VALUE"] == 16

    def test_port_interfaces(self, hierarchy_dataflow, hierarchy_specification):
        connections = _kpm_parse_connections_between_nodes(
            hierarchy_dataflow, hierarchy_specification
        )

        assert connections.ports == {
            "complex_sub": {"cs_in_1": ("counter", "c_out_1")},
            "c_mod_3": {
                "c_int_in_1": ("c_mod_2", "c_int_out_2"),
                "c_int_in_2": ("c_mod_1", "c_int_out_1"),
            },
            "sub_2": {
                "cs_s2_int_in_1": ("sub_1", "cs_s1_int_out_1"),
                "cs_s2_int_in_2": ("sub_1", "cs_s1_int_out_2"),
            },
            "s1_mod_2": {"cs_s1_mint_in_1": ("s1_mod_1", "cs_s1_mint_out_1")},
            "s1_mod_3": {"cs_s1_mint_in_2": ("s1_mod_1", "cs_s1_mint_out_1")},
            "s2_mod_2": {
                "cs_s2_mint_in_1": ("s2_mod_1", "cs_s2_mint_out_1"),
                "cs_s2_mint_in_2": ("s2_mod_1", "cs_s2_mint_out_2"),
            },
        }

        assert connections.interfaces == {}

    def test_externals(self, hierarchy_dataflow, hierarchy_specification):
        df = graph_to_isolated_dataflow(
            hierarchy_dataflow, get_entry_graph(hierarchy_dataflow)["id"]
        )
        assert (
            DeepDiff(
                _kpm_gather_all_graph_externals(df, hierarchy_specification).to_dict(),
                {
                    "ports": {
                        "complex_sub": {"cs_out_1": "ex_in_1"},
                        "counter": {"c_in_1": "ex_out_1", "c_in_2": "ex_out_2"},
                    },
                    "external": {
                        "ports": {"in": ["ex_out_1", "ex_out_2"], "out": ["ex_in_1"]},
                    },
                },
                ignore_order=True,
            )
            == {}
        )

    def test_constants(self, hierarchy_dataflow):
        assert _kpm_connections_to_constant(hierarchy_dataflow).ports == {
            "sub_1": {"cs_s1_int_const_in": 1},
            "c_mod_3": {"c_int_const_in": 1},
        }


class TestComplexDesignExport:
    @pytest.fixture
    def _generated_design(self, complex_dataflow, complex_specification):
        return kpm_dataflow_to_design(complex_dataflow, complex_specification)

    def test_duplicate_ips_locally(self, _generated_design: DesignDescription):
        """Check if instance name suffixing works correctly for duplicates in the top level"""

        assert len(_generated_design.ips.keys()) == 5
        for ip in ("s1_mod_3", "s1_mod_3_2", "s1_mod_3_3"):
            assert ip in _generated_design.ips.keys()

    def test_duplicate_ips_deeper(self, _generated_design: DesignDescription):
        """Checks if the above also works on deeper hierarchy levels
        and that the instance name resolution is not done globally"""

        for ip in ("s1_mod_3", "s1_mod_3_2"):
            assert ip in _generated_design.design.hierarchies["SUB"].design.hierarchies["SUB"].ips

    def test_hierarchies_same_names(self, _generated_design: DesignDescription):
        """Checks if multiple nested hierarchies having the same name works correctly"""

        sub1 = _generated_design.design.hierarchies.get("SUB")
        assert sub1 is not None
        sub2 = sub1.design.hierarchies.get("SUB")
        assert sub2 is not None
        assert sub1 != sub2

        assert "SUBEMPTY" in sub1.design.hierarchies
        assert "SUBEMPTY" in sub1.design.hierarchies["SUBEMPTY"].design.hierarchies

    def test_orphan_metanodes_preserved(self, _generated_design: DesignDescription):
        """Checks if top-level input/output metanodes that
        aren't connected to anything are preserved in the yaml"""

        assert "cout" in _generated_design.external.ports.output
        assert "cin" in _generated_design.external.ports.input

    def test_orphan_inout_throws(self, complex_dataflow, complex_specification):
        """Checks if an unconnected top-level inout port is detected appropriately"""

        entry = get_entry_graph(complex_dataflow)
        entry["nodes"].append(
            KPMDataflowExternalMetanode(EXT_INOUT_NAME, "barafoo").to_json_format()
        )

        with pytest.raises(
            KPMExportException, match="While parsing the top level, an exception occurred"
        ) as exc:
            kpm_dataflow_to_design(complex_dataflow, complex_specification)

        assert exc.value.__cause__.args[0].startswith("An inout port has an invalid")

    def test_multiple_connection_preservation(self, _generated_design: DesignDescription):
        """Checks if a port both exposed and connected to preserved all its connections"""

        ports = _generated_design.design.hierarchies["SUB"].design.hierarchies["SUB"].design.ports

        assert (
            "s1_mod_3",
            {
                "cs_s1_mint_in_2": ("s1_mod_3_2", "cs_s1_f_int_out_2"),
                "cs_s1_f_int_out_2": ("s1_mod_3_2", "cs_s1_mint_in_2"),
            },
        ) in ports.items()
        assert ("cs_s1_mint_in_2", "cs_s1_mint_in_2") in ports["s1_mod_3_2"].items()

    def test_implicit_metanode_name_generation(self, _generated_design: DesignDescription):
        """Checks if an external metanode without a user-defined name correctly gets assigned a name from the connected port"""

        assert "cs_s1_f_int_out_2" in _generated_design.external.ports.output
        assert _generated_design.design.ports["s1_mod_3_3"] == {
            "cs_s1_f_int_out_2": "cs_s1_f_int_out_2"
        }

    def test_subgraph_external_with_a_manual_name(self, _generated_design: DesignDescription):
        """Checks if a subgraph with a user-defined external port with a custom external name gets preserved"""

        NAME = "customized_ext_name_port"
        assert NAME in _generated_design.design.hierarchies["SUB"].external.ports.input
        assert _generated_design.design.ports["SUB"][NAME] == "c_unt_in"
        assert (
            _generated_design.design.hierarchies["SUB"].design.ports["SUB"]["cs_s2_f_int_in_2"]
            == NAME
        )

    def test_subgraph_externals_legacy_notation(self, _generated_design: DesignDescription):
        """Checks if a subgraph with a legacy external port (just exposed, without using the subgraph port metanode) gets preserved"""

        NAME = "legacy_external_type"
        assert NAME in _generated_design.design.hierarchies["SUB"].external.ports.input
        assert _generated_design.design.hierarchies["SUB"].design.ports["s1_mod_2"] == {
            "cs_s1_mint_in_1": NAME
        }


class TestMultipleIllegalsDataflow:
    """Tests a dataflow containing many illegal connections to
    verify if we correctly catch the errors"""

    @pytest.fixture
    def mischievous_dataflow(self) -> JsonType:
        return get_dataflow_test("dataflow_multiple_invalid_designs")

    @pytest.fixture
    def dataflow(self, name: str, mischievous_dataflow: JsonType) -> JsonType:
        for node in get_entry_graph(mischievous_dataflow)["nodes"]:
            if is_subgraph_node(node) and node["instanceName"] == name:
                return graph_to_isolated_dataflow(mischievous_dataflow, node["subgraph"])
        raise UnreachableError

    @pytest.fixture
    def spec(self, hierarchy_specification: JsonType) -> JsonType:
        return hierarchy_specification

    @pytest.mark.parametrize("name", ["overconnected_ports"])
    def test_overconnected_ports(self, dataflow: JsonType, spec: JsonType):
        with pytest.raises(KPMExportException, match="Cannot repr.*as.*conn.*to something else"):
            _kpm_parse_connections_between_nodes(dataflow, spec)

    @pytest.mark.parametrize(
        ["name", "err"],
        [
            ("unnamed_to_over_1", "metanode.*multiple other ports"),
            ("sub_exposed_and_conn", "subgraph.*exposed.*conn.*any other nodes"),
            *zip(
                ("external_to_meta_1", "external_to_meta_2", "sub_meta_2_sub_meta"),
                ["metanode.*connected to another metanode"] * 3,
            ),
            *zip(
                ("unconnected_inout", "inout_with_over_1_con"),
                ["inout.*invalid amount of conn"] * 2,
            ),
        ],
    )
    def test_externals(self, dataflow: JsonType, spec: JsonType, err: str):
        with pytest.raises(KPMExportException, match=err):
            _kpm_gather_all_graph_externals(dataflow, spec)

    @pytest.mark.parametrize("name", ["empty_external"])
    def test_empty_external_warn(self, dataflow: JsonType, spec: JsonType, caplog: Any):
        _kpm_gather_all_graph_externals(dataflow, spec)
        for name, level, msg in caplog.record_tuples:
            if (
                name == "topwrap.kpm_dataflow_parser"
                and level == logging.WARNING
                and msg.startswith(
                    "An external metanode without an external name that isn't connected"
                )
            ):
                break
        else:
            assert False, "Did not raise a warning"
