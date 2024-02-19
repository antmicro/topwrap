# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from typing import List

import pytest

from topwrap.hdl_parsers_utils import PortDefinition, PortDirection
from topwrap.verilog_parser import VerilogModule
from topwrap.vhdl_parser import VHDLModule


class TestVerilogParse:
    AXI_MODULE_PORTS = set(
        [
            PortDefinition("clk", "0", "0", PortDirection.IN),
            PortDefinition("rst", "0", "0", PortDirection.IN),
            # AXI slave interface
            PortDefinition("s_axi_awid", "(AXI_ID_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_awaddr", "(ADDR_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_awlen", "7", "0", PortDirection.IN),
            PortDefinition("s_axi_awsize", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_awburst", "1", "0", PortDirection.IN),
            PortDefinition("s_axi_awlock", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_awcache", "3", "0", PortDirection.IN),
            PortDefinition("s_axi_awprot", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_awvalid", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_awready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_wdata", "(AXI_DATA_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_wstrb", "(AXI_STRB_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_wlast", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_wvalid", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_wready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_bid", "(AXI_ID_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s_axi_bresp", "1", "0", PortDirection.OUT),
            PortDefinition("s_axi_bvalid", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_bready", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_arid", "(AXI_ID_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_araddr", "(ADDR_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_arlen", "7", "0", PortDirection.IN),
            PortDefinition("s_axi_arsize", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_arburst", "1", "0", PortDirection.IN),
            PortDefinition("s_axi_arlock", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_arcache", "3", "0", PortDirection.IN),
            PortDefinition("clk", "0", "0", PortDirection.IN),
            PortDefinition("rst", "0", "0", PortDirection.IN),
            # AXI slave interface
            PortDefinition("s_axi_awid", "(AXI_ID_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_awaddr", "(ADDR_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_awlen", "7", "0", PortDirection.IN),
            PortDefinition("s_axi_awsize", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_awburst", "1", "0", PortDirection.IN),
            PortDefinition("s_axi_awlock", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_awcache", "3", "0", PortDirection.IN),
            PortDefinition("s_axi_awprot", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_awvalid", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_awready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_wdata", "(AXI_DATA_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_wstrb", "(AXI_STRB_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_wlast", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_wvalid", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_wready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_bid", "(AXI_ID_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s_axi_bresp", "1", "0", PortDirection.OUT),
            PortDefinition("s_axi_bvalid", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_bready", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_arid", "(AXI_ID_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_araddr", "(ADDR_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s_axi_arlen", "7", "0", PortDirection.IN),
            PortDefinition("s_axi_arsize", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_arburst", "1", "0", PortDirection.IN),
            PortDefinition("s_axi_arlock", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_arcache", "3", "0", PortDirection.IN),
            PortDefinition("s_axi_arprot", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_arvalid", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_arready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_rid", "(AXI_ID_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s_axi_rdata", "(AXI_DATA_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s_axi_rresp", "1", "0", PortDirection.OUT),
            PortDefinition("s_axi_rlast", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_rvalid", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_rready", "0", "0", PortDirection.IN),
            # AXI lite master interface
            PortDefinition("m_axil_awaddr", "(ADDR_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_awprot", "2", "0", PortDirection.OUT),
            PortDefinition("m_axil_awvalid", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_awready", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_wdata", "(AXIL_DATA_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_wstrb", "(AXIL_STRB_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_wvalid", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_wready", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_bresp", "1", "0", PortDirection.IN),
            PortDefinition("m_axil_bvalid", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_bready", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_araddr", "(ADDR_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_arprot", "2", "0", PortDirection.OUT),
            PortDefinition("m_axil_arvalid", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_arready", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_rdata", "(AXIL_DATA_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("m_axil_rresp", "1", "0", PortDirection.IN),
            PortDefinition("m_axil_rvalid", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_rready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_arprot", "2", "0", PortDirection.IN),
            PortDefinition("s_axi_arvalid", "0", "0", PortDirection.IN),
            PortDefinition("s_axi_arready", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_rid", "(AXI_ID_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s_axi_rdata", "(AXI_DATA_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s_axi_rresp", "1", "0", PortDirection.OUT),
            PortDefinition("s_axi_rlast", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_rvalid", "0", "0", PortDirection.OUT),
            PortDefinition("s_axi_rready", "0", "0", PortDirection.IN),
            # AXI lite master interface
            PortDefinition("m_axil_awaddr", "(ADDR_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_awprot", "2", "0", PortDirection.OUT),
            PortDefinition("m_axil_awvalid", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_awready", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_wdata", "(AXIL_DATA_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_wstrb", "(AXIL_STRB_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_wvalid", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_wready", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_bresp", "1", "0", PortDirection.IN),
            PortDefinition("m_axil_bvalid", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_bready", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_araddr", "(ADDR_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("m_axil_arprot", "2", "0", PortDirection.OUT),
            PortDefinition("m_axil_arvalid", "0", "0", PortDirection.OUT),
            PortDefinition("m_axil_arready", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_rdata", "(AXIL_DATA_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("m_axil_rresp", "1", "0", PortDirection.IN),
            PortDefinition("m_axil_rvalid", "0", "0", PortDirection.IN),
            PortDefinition("m_axil_rready", "0", "0", PortDirection.OUT),
        ]
    )

    AXI_MODULE_PARAMS = {
        "ADDR_WIDTH": 32,
        "AXI_DATA_WIDTH": 32,
        "AXI_STRB_WIDTH": "(AXI_DATA_WIDTH/8)",
        "AXI_ID_WIDTH": 8,
        "AXIL_DATA_WIDTH": 32,
        "AXIL_STRB_WIDTH": "(AXIL_DATA_WIDTH/8)",
        "CONVERT_BURST": 1,
        "CONVERT_NARROW_BURST": 0,
    }

    @pytest.fixture
    def axi_module(self) -> VerilogModule:
        from topwrap.verilog_parser import VerilogModuleGenerator

        verilog_modules = VerilogModuleGenerator().get_modules(
            "tests/data/data_parse/axi_axil_adapter.v"
        )
        assert len(verilog_modules) == 1
        return verilog_modules[0]

    @pytest.fixture
    def seg7_4d_ctrl_modules(self) -> List[VerilogModule]:
        from topwrap.verilog_parser import VerilogModuleGenerator

        verilog_modules = VerilogModuleGenerator().get_modules(
            "tests/data/data_parse/seg7_4d_ctrl.v"
        )
        assert len(verilog_modules) > 0
        return verilog_modules

    def test_axi_module_parameters(self, axi_module):
        assert axi_module.get_parameters() == self.AXI_MODULE_PARAMS

    def test_axi_module_name(self, axi_module):
        assert axi_module.get_module_name() == "axi_axil_adapter"

    def test_axi_module_ports(self, axi_module):
        assert axi_module.get_ports() == self.AXI_MODULE_PORTS

    def test_verilog_parse_multiple_modules(self, seg7_4d_ctrl_modules):
        assert len(seg7_4d_ctrl_modules) == 9

        # check if arbitrary modules (1st and 5th counting from 0) were parsed correcly
        seg7_4d_ctrl_raw_test = seg7_4d_ctrl_modules[1]
        assert seg7_4d_ctrl_raw_test.get_module_name() == "seg7_4d_ctrl_raw_test"
        assert seg7_4d_ctrl_raw_test.get_parameters() == {}
        assert seg7_4d_ctrl_raw_test.get_ports() == set(
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
        assert seg7_4d_ctrl_dec_tc.get_module_name() == "seg7_4d_ctrl_dec_tc"
        assert seg7_4d_ctrl_dec_tc.get_parameters() == {"CDBITS": 18, "POL": 0, "SELECT_POL": 0}
        assert seg7_4d_ctrl_dec_tc.get_ports() == set(
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
    AXI_MODULE_PORTS = set(
        [
            PortDefinition("S_AXIS_ACLK", "0", "0", PortDirection.IN),
            PortDefinition("S_AXIS_TDATA", "(C_S_AXIS_TDATA_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("S_AXIS_TVALID", "0", "0", PortDirection.IN),
            PortDefinition("S_AXIS_TLAST", "0", "0", PortDirection.IN),
            PortDefinition("S_AXIS_TUSER", "0", "0", PortDirection.IN),
            PortDefinition("S_AXIS_TREADY", "0", "0", PortDirection.OUT),
            PortDefinition("FSYNC_O", "0", "0", PortDirection.OUT),
            PortDefinition("HSYNC_O", "0", "0", PortDirection.OUT),
            PortDefinition("VSYNC_O", "0", "0", PortDirection.OUT),
            PortDefinition("DE_O", "0", "0", PortDirection.OUT),
            PortDefinition("DATA_O", "(C_S_AXIS_TDATA_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("CTL_O", "3", "0", PortDirection.OUT),
            PortDefinition("VGUARD_O", "0", "0", PortDirection.OUT),
            PortDefinition("DGUARD_O", "0", "0", PortDirection.OUT),
            PortDefinition("DIEN_O", "0", "0", PortDirection.OUT),
            PortDefinition("DIH_O", "0", "0", PortDirection.OUT),
            PortDefinition("LOCKED_I", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_aclk", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_aresetn", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_awaddr", "(C_S00_AXI_ADDR_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s00_axi_awprot", "2", "0", PortDirection.IN),
            PortDefinition("s00_axi_awvalid", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_awready", "0", "0", PortDirection.OUT),
            PortDefinition("s00_axi_wdata", "(C_S00_AXI_DATA_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s00_axi_wstrb", "((C_S00_AXI_DATA_WIDTH/8)-1)", "0", PortDirection.IN),
            PortDefinition("s00_axi_wvalid", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_wready", "0", "0", PortDirection.OUT),
            PortDefinition("s00_axi_bresp", "1", "0", PortDirection.OUT),
            PortDefinition("s00_axi_bvalid", "0", "0", PortDirection.OUT),
            PortDefinition("s00_axi_bready", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_araddr", "(C_S00_AXI_ADDR_WIDTH-1)", "0", PortDirection.IN),
            PortDefinition("s00_axi_arprot", "2", "0", PortDirection.IN),
            PortDefinition("s00_axi_arvalid", "0", "0", PortDirection.IN),
            PortDefinition("s00_axi_arready", "0", "0", PortDirection.OUT),
            PortDefinition("s00_axi_rdata", "(C_S00_AXI_DATA_WIDTH-1)", "0", PortDirection.OUT),
            PortDefinition("s00_axi_rresp", "1", "0", PortDirection.OUT),
            PortDefinition("s00_axi_rvalid", "0", "0", PortDirection.OUT),
            PortDefinition("s00_axi_rready", "0", "0", PortDirection.IN),
        ]
    )

    @pytest.fixture
    def axi_module(self) -> VHDLModule:
        return VHDLModule("tests/data/data_parse/axi_dispctrl_v1_0.vhd")

    def test_axi_module_parameters(self, axi_module):
        assert axi_module.get_parameters() == {
            "C_S_AXIS_TDATA_WIDTH": 32,
            "C_S00_AXI_DATA_WIDTH": 32,
            "C_S00_AXI_ADDR_WIDTH": 7,
        }

    def test_axi_module_name(self, axi_module):
        assert axi_module.get_module_name() == "axi_dispctrl_v1_0"

    def test_axi_module_ports(self, axi_module):
        assert axi_module.get_ports() == self.AXI_MODULE_PORTS
