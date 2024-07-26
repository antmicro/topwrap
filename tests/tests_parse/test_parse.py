# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.hdl_parsers_utils import PortDefinition, PortDirection

from .parse_common import AXI_AXIL_ADAPTER_PORTS, AXI_DISPCTRL_PORTS


class TestVerilogParse:
    AXI_AXIL_ADAPTER_PARAMS = {
        "ADDR_WIDTH": 32,
        "AXI_DATA_WIDTH": 32,
        "AXI_STRB_WIDTH": "(AXI_DATA_WIDTH/8)",
        "AXI_ID_WIDTH": 8,
        "AXIL_DATA_WIDTH": 32,
        "AXIL_STRB_WIDTH": "(AXIL_DATA_WIDTH/8)",
        "CONVERT_BURST": 1,
        "CONVERT_NARROW_BURST": 0,
    }

    def test_axi_module_parameters(self, axi_verilog_module):
        assert axi_verilog_module.parameters == self.AXI_AXIL_ADAPTER_PARAMS

    def test_axi_module_name(self, axi_verilog_module):
        assert axi_verilog_module.module_name == "axi_axil_adapter"

    def test_axi_module_ports(self, axi_verilog_module):
        assert axi_verilog_module.ports == set(AXI_AXIL_ADAPTER_PORTS)

    def test_verilog_parse_multiple_modules(self, seg7_4d_ctrl_modules):
        assert len(seg7_4d_ctrl_modules) == 9

        # check if arbitrary modules (1st and 5th counting from 0) were parsed correctly
        seg7_4d_ctrl_raw_test = seg7_4d_ctrl_modules[1]
        assert seg7_4d_ctrl_raw_test.module_name == "seg7_4d_ctrl_raw_test"
        assert seg7_4d_ctrl_raw_test.parameters == {}
        assert seg7_4d_ctrl_raw_test.ports == set(
            [
                PortDefinition("clk", "0", "0", PortDirection.IN),
                PortDefinition("on_mask", "3", "0", PortDirection.IN),
                PortDefinition("dp_in", "3", "0", PortDirection.IN),
                PortDefinition("sign_mask", "3", "0", PortDirection.IN),
                PortDefinition("seg", "0", "6", PortDirection.OUT),
                PortDefinition("select", "3", "0", PortDirection.OUT),
                PortDefinition("dp", "0", "0", PortDirection.OUT),
            ]
        )

        seg7_4d_ctrl_dec_tc = seg7_4d_ctrl_modules[5]
        assert seg7_4d_ctrl_dec_tc.module_name == "seg7_4d_ctrl_dec_tc"
        assert seg7_4d_ctrl_dec_tc.parameters == {"CDBITS": 18, "POL": 0, "SELECT_POL": 0}
        assert seg7_4d_ctrl_dec_tc.ports == set(
            [
                PortDefinition("clk", "0", "0", PortDirection.IN),
                PortDefinition("d", "7", "0", PortDirection.IN),
                PortDefinition("dp_in", "3", "0", PortDirection.IN),
                PortDefinition("seg", "0", "6", PortDirection.OUT),
                PortDefinition("select", "3", "0", PortDirection.OUT),
                PortDefinition("dp", "0", "0", PortDirection.OUT),
            ]
        )


class TestVHDLParse:
    def test_axi_module_parameters(self, axi_vhdl_module):
        assert axi_vhdl_module.parameters == {
            "C_S_AXIS_TDATA_WIDTH": 32,
            "C_S00_AXI_DATA_WIDTH": 32,
            "C_S00_AXI_ADDR_WIDTH": 7,
        }

    def test_axi_module_name(self, axi_vhdl_module):
        assert axi_vhdl_module.module_name == "axi_dispctrl_v1_0"

    def test_axi_module_ports(self, axi_vhdl_module):
        assert axi_vhdl_module.ports == set(AXI_DISPCTRL_PORTS)
