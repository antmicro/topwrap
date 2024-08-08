# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.kpm_common import get_all_graph_nodes
from topwrap.kpm_dataflow_parser import (
    _kpm_connections_to_constant,
    _kpm_connections_to_external,
    _kpm_connections_to_ports_ifaces,
    _kpm_nodes_to_ips,
    _kpm_properties_to_parameters,
)

from .common import AXI_NAME, PS7_NAME, PWM_NAME


class TestPWMDataflowExport:
    """Tests that check validity of generated design description YAML from PWM dataflow
    (i.e. PWM dataflow export feature).
    """

    def test_parameters(self, pwm_dataflow):
        """Check whether generated parameters values match the overridden values from
        `examples/pwm/project.yml` and default values from IP core description YAMLs.
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

    def test_nodes_to_ips(self, pwm_design_yaml, pwm_dataflow, pwm_specification):
        """Check whether generated IP cores names in "ips" section of a design description YAML
        match the values from `examples/pwm/project.yml`.
        """

        ips = _kpm_nodes_to_ips(pwm_dataflow, pwm_specification)
        assert ips.keys() == pwm_design_yaml["ips"].keys()

    def test_port_interfaces(self, pwm_dataflow, pwm_specification):
        """Check whether generated connection descriptions in "ports" and "interfaces" sections
        of a design description YAML match the values from `examples/pwm/project.yml`.
        """
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

    def test_externals(self, pwm_dataflow, pwm_specification):
        """Check whether generated external ports/interfaces descriptions in "externals" section
        of a design description YAML match the values from `examples/pwm/project.yml`.
        """
        assert _kpm_connections_to_external(pwm_dataflow, pwm_specification) == {
            "ports": {PWM_NAME: {"pwm": "pwm"}},
            "interfaces": {},
            "external": {
                "ports": {"in": [], "out": ["pwm"], "inout": []},
                "interfaces": {"in": [], "out": [], "inout": []},
            },
        }

    def test_constants(self, pwm_dataflow, pwm_specification):
        """Check whether generated constant ports descriptions match the values
        from `examples/pwm/project.yml`.
        """
        assert _kpm_connections_to_constant(pwm_dataflow, pwm_specification) == {"ports": {}}


class TestHDMIDataflowExport:
    """Tests that check validity of generated design description YAML from HDMI dataflow
    (i.e. HDMI dataflow export feature).
    """

    def test_parameters(self, hdmi_dataflow):
        """Check whether some generated parameters values match the values from
        `examples/hdmi/project.yml`.
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

    def test_nodes_to_ips(self, hdmi_design_yaml, hdmi_dataflow, hdmi_specification):
        """Check whether generated IP cores names in "ips" section of a design description YAML
        match the values from `examples/hdmi/project.yml`.
        """
        ips = _kpm_nodes_to_ips(hdmi_dataflow, hdmi_specification)
        assert ips.keys() == hdmi_design_yaml["ips"].keys()

    def test_interfaces(self, hdmi_design_yaml, hdmi_dataflow, hdmi_specification):
        """Check whether generated connection descriptions in "interfaces" sections
        of a design description YAML match the values from `examples/hdmi/project.yml`.

        For now we don't test validity of "ports" section, since in `examples/pwm/project.yml`
        some ports are driven by constants. This feature is not yet supported in KPM.
        """
        connections = _kpm_connections_to_ports_ifaces(hdmi_dataflow, hdmi_specification)
        assert connections["interfaces"] == hdmi_design_yaml["design"]["interfaces"]

    def test_externals(self, hdmi_dataflow, hdmi_specification):
        """Check whether generated external ports/interfaces descriptions in "externals" section
        of a design description YAML match the values from `examples/hdmi/project.yml`.
        """
        assert _kpm_connections_to_external(hdmi_dataflow, hdmi_specification) == {
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
            "interfaces": {},
            "external": {
                "ports": {
                    "in": [],
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
                    "inout": [],
                },
                "interfaces": {"in": [], "out": [], "inout": []},
            },
        }

    def test_constants(self, hdmi_dataflow, hdmi_specification):
        """Check whether generated constant ports description match the values
        from `examples/hdmi/project.yml`.
        """
        assert _kpm_connections_to_constant(hdmi_dataflow, hdmi_specification) == {
            "ports": {
                "reset0": {
                    "aux_reset_in": "0",
                    "dcm_locked": "1",
                    "ext_reset_in": "0",
                    "mb_debug_sys_rst": "0",
                },
                "reset1": {
                    "aux_reset_in": "0",
                    "dcm_locked": "1",
                    "ext_reset_in": "0",
                    "mb_debug_sys_rst": "0",
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

    def test_nodes_to_ips(self, hierarchy_design_yaml, hierarchy_dataflow, hierarchy_specification):
        ips = _kpm_nodes_to_ips(hierarchy_dataflow, hierarchy_specification)
        assert ips.keys() == hierarchy_design_yaml["ips"].keys()

    def test_port_interfaces(self, hierarchy_dataflow, hierarchy_specification):
        connections = _kpm_connections_to_ports_ifaces(hierarchy_dataflow, hierarchy_specification)

        assert connections["ports"] == {
            "complex_sub": {"cs_in_1": ["counter", "c_out_1"]},
            "c_mod_3": {
                "c_int_in_1": ["c_mod_2", "c_int_out_2"],
                "c_int_in_2": ["c_mod_1", "c_int_out_1"],
            },
            "sub_2": {
                "cs_s2_int_in_1": ["sub_1", "cs_s1_int_out_1"],
                "cs_s2_int_in_2": ["sub_1", "cs_s1_int_out_2"],
            },
            "s1_mod_2": {"cs_s1_mint_in_1": ["s1_mod_1", "cs_s1_mint_out_1"]},
            "s1_mod_3": {"cs_s1_mint_in_2": ["s1_mod_1", "cs_s1_mint_out_1"]},
            "s2_mod_2": {
                "cs_s2_mint_in_1": ["s2_mod_1", "cs_s2_mint_out_1"],
                "cs_s2_mint_in_2": ["s2_mod_1", "cs_s2_mint_out_2"],
            },
        }

        assert connections["interfaces"] == {}

    def test_externals(self, hierarchy_dataflow, hierarchy_specification):
        assert _kpm_connections_to_external(hierarchy_dataflow, hierarchy_specification) == {
            "ports": {
                "complex_sub": {"cs_out_1": "ex_in_1"},
                "counter": {"c_in_1": "ex_out_1", "c_in_2": "ex_out_2"},
            },
            "interfaces": {},
            "external": {
                "ports": {"in": ["ex_out_1", "ex_out_2"], "out": ["ex_in_1"], "inout": []},
                "interfaces": {"in": [], "out": [], "inout": []},
            },
        }

    def test_constants(self, hierarchy_dataflow, hierarchy_specification):
        assert _kpm_connections_to_constant(hierarchy_dataflow, hierarchy_specification) == {
            "ports": {}
        }
