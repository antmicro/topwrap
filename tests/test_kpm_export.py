# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import os

from fpga_topwrap.kpm_dataflow_parser import (
    _kpm_connections_to_external,
    _kpm_connections_to_ports_ifaces,
    _kpm_nodes_to_ips,
    _kpm_properties_to_parameters,
)
from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

AXI_NAME = "axi_bridge"
PS7_NAME = "ps7"
PWM_NAME = "litex_pwm_top"


def ipcore_names_to_yamls(ipcores_yamls: list):
    """Return a dict with "`ipcore_name`: `ipcore_descr_yaml`" key-value pairs"""

    def basename_without_ext(name: str):
        return os.path.splitext(os.path.basename(name))[0]

    return {basename_without_ext(yamlfile): yamlfile for yamlfile in ipcores_yamls}


class TestPWMDataflowExport:
    def test_parameters(self, pwm_dataflow):
        [axi_node] = list(
            filter(lambda node: node["name"] == AXI_NAME, pwm_dataflow["graph"]["nodes"])
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

    def test_nodes_to_ips(self, pwm_ipcores_yamls, pwm_design_yaml, pwm_dataflow):
        pwm_ipcores_names_to_yamls = ipcore_names_to_yamls(pwm_ipcores_yamls)
        ips = _kpm_nodes_to_ips(pwm_dataflow, pwm_ipcores_names_to_yamls)
        assert ips.keys() == pwm_design_yaml["ips"].keys()

    def test_port_interfaces(self, pwm_dataflow, pwm_ipcores_yamls):
        pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
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

    def test_externals(self, pwm_dataflow, pwm_ipcores_yamls):
        pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
        assert _kpm_connections_to_external(pwm_dataflow, pwm_specification) == {
            "ports": {PWM_NAME: {"pwm": "pwm"}},
            "interfaces": {},
            "external": {
                "ports": {"in": [], "out": ["pwm"], "inout": []},
                "interfaces": {"in": [], "out": [], "inout": []},
            },
        }


class TestHDMIDataflowExport:
    def test_parameters(self, hdmi_dataflow):
        [axi_node] = list(
            filter(
                lambda node: node["name"] == "axi_interconnect0", hdmi_dataflow["graph"]["nodes"]
            )
        )
        parameters = _kpm_properties_to_parameters(axi_node["properties"])
        assert parameters["ADDR_WIDTH"] == 32
        assert parameters["M_ADDR_WIDTH"] == {"value": int("0x100000001000000010", 16), "width": 96}

    def test_nodes_to_ips(self, hdmi_design_yaml, hdmi_dataflow, hdmi_ipcores_yamls):
        hdmi_ipcores_names_to_yamls = ipcore_names_to_yamls(hdmi_ipcores_yamls)
        ips = _kpm_nodes_to_ips(hdmi_dataflow, hdmi_ipcores_names_to_yamls)
        assert ips.keys() == hdmi_design_yaml["ips"].keys()

    def test_port_interfaces(self, hdmi_design_yaml, hdmi_dataflow, hdmi_ipcores_yamls):
        hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
        connections = _kpm_connections_to_ports_ifaces(hdmi_dataflow, hdmi_specification)
        assert connections["interfaces"] == hdmi_design_yaml["interfaces"]

    def test_externals(self, hdmi_dataflow, hdmi_ipcores_yamls):
        hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
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
