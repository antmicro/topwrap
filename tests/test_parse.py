# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
from typing import List
from fpga_topwrap.verilog_parser import VerilogModule
from fpga_topwrap.vhdl_parser import VHDLModule


class TestVerilogParse:
    @pytest.fixture
    def axi_axil_adapter_module(self) -> VerilogModule:
        from fpga_topwrap.verilog_parser import VerilogModuleGenerator
        verilog_modules = VerilogModuleGenerator().get_modules('tests/data/axi_axil_adapter.v')
        assert len(verilog_modules) == 1
        return verilog_modules[0]

    @pytest.fixture
    def axi_axil_adapter_params(self, axi_axil_adapter_module) -> dict:
        return axi_axil_adapter_module.get_parameters()

    @pytest.fixture
    def axi_axil_adapter_ports(self, axi_axil_adapter_module) -> dict:
        return axi_axil_adapter_module.get_ports()

    @pytest.fixture
    def axi_axil_adapter_ports_by_dir(self, axi_axil_adapter_ports) -> dict:
        from fpga_topwrap.verilog_parser import group_ports_by_dir
        return group_ports_by_dir(axi_axil_adapter_ports)

    @pytest.fixture
    def seg7_4d_ctrl_modules(self) -> List[VerilogModule]:
        from fpga_topwrap.verilog_parser import VerilogModuleGenerator
        verilog_modules = VerilogModuleGenerator().get_modules('tests/data/seg7_4d_ctrl.v')
        assert len(verilog_modules) > 0
        return verilog_modules


    def test_axi_axil_adapter_parameters(self, axi_axil_adapter_params):
        assert len(axi_axil_adapter_params) == 8
        assert ('ADDR_WIDTH', 32) in axi_axil_adapter_params.items()
        assert ('AXI_STRB_WIDTH', '(AXI_DATA_WIDTH/8)') in axi_axil_adapter_params.items()
        assert ('CONVERT_NARROW_BURST', 0) in axi_axil_adapter_params.items()


    def test_axi_axil_adapter_ports(self, axi_axil_adapter_ports_by_dir):
        assert axi_axil_adapter_ports_by_dir['inout'] == []
        
        assert len(axi_axil_adapter_ports_by_dir['in']) == 34
        assert {'name': 'clk', 'bounds': ('0', '0')} in axi_axil_adapter_ports_by_dir['in']
        assert {'name': 's_axi_awid', 'bounds': ('(AXI_ID_WIDTH-1)', '0')} in axi_axil_adapter_ports_by_dir['in']
        assert {'name': 's_axi_arlen', 'bounds': ('7', '0')} in axi_axil_adapter_ports_by_dir['in']

        assert len(axi_axil_adapter_ports_by_dir['out']) == 22
        assert {'name': 's_axi_awready', 'bounds': ('0', '0')} in axi_axil_adapter_ports_by_dir['out']
        assert {'name': 's_axi_rid', 'bounds': ('(AXI_ID_WIDTH-1)', '0')} in axi_axil_adapter_ports_by_dir['out']
        assert {'name': 'm_axil_arprot', 'bounds': ('2', '0')} in axi_axil_adapter_ports_by_dir['out']


    def test_axi_axil_adapter_iface_deduce(self, axi_axil_adapter_ports, axi_axil_adapter_ports_by_dir):
        from fpga_topwrap.interface_grouper import InterfaceGrouper
        from fpga_topwrap.hdl_parsers_utils import group_ports_to_ifaces
        iface_grouper = InterfaceGrouper(False, True, None)

        # `hdl_file` argument can be `None` here since we don't use yosys for parsing here
        iface_mappings = iface_grouper.get_interface_mappings(None, axi_axil_adapter_ports)
        ifaces = group_ports_to_ifaces(iface_mappings, axi_axil_adapter_ports_by_dir)

        assert list(ifaces.keys()) == ['s_axi', 'm_axil']
        assert len(ifaces['s_axi']['in']) == 24
        assert len(ifaces['s_axi']['out']) == 11
        assert len(ifaces['m_axil']['in']) == 8
        assert len(ifaces['m_axil']['out']) == 11


    def test_axi_axil_adapter_specified_ifaces(self, axi_axil_adapter_ports, axi_axil_adapter_ports_by_dir):
        from fpga_topwrap.interface_grouper import InterfaceGrouper
        from fpga_topwrap.hdl_parsers_utils import group_ports_to_ifaces
        iface_grouper = InterfaceGrouper(False, False, ('m_axil', ))
        
        # `hdl_file` argument can be `None` here since we don't use yosys for parsing here
        iface_mappings = iface_grouper.get_interface_mappings(None, axi_axil_adapter_ports)
        ifaces = group_ports_to_ifaces(iface_mappings, axi_axil_adapter_ports_by_dir)

        assert list(ifaces.keys()) == ['m_axil']
        assert len(ifaces['m_axil']['in']) == 8
        assert len(ifaces['m_axil']['out']) == 11


    def test_verilog_parse_multiple_modules(self, seg7_4d_ctrl_modules):
        from fpga_topwrap.verilog_parser import group_ports_by_dir
        assert len(seg7_4d_ctrl_modules) == 9

        # check if one of the modules (the first one) was parsed correcly
        seg7_4d_ctrl_raw = seg7_4d_ctrl_modules[0]
        assert seg7_4d_ctrl_raw.get_module_name() == "seg7_4d_ctrl_raw"
        assert seg7_4d_ctrl_raw.get_parameters() == {'CDBITS': 18, 'POL': 0, 'SELECT_POL': 0}

        ports_by_dir = group_ports_by_dir(seg7_4d_ctrl_raw.get_ports())
        assert ports_by_dir['inout'] == []
        assert ports_by_dir['in'] == [
            {'name': 'clk', 'bounds': ('0', '0')},
            {'name': 'd', 'bounds': ('15', '0')},
            {'name': 'on_mask', 'bounds': ('3', '0')}, 
            {'name': 'dp_in', 'bounds': ('3', '0')},
            {'name': 'sign_mask', 'bounds': ('3', '0')}
        ]
        assert ports_by_dir['out'] == [
            {'name': 'seg', 'bounds': ('0', '6')},
            {'name': 'select', 'bounds': ('3', '0')}, 
            {'name': 'dp', 'bounds': ('0', '0')}
        ]


class TestVHDLParse:
    @pytest.fixture
    def axi_dispctrl_module(self) -> VHDLModule:
        return VHDLModule('tests/data/axi_dispctrl_v1_0.vhd')
   
    @pytest.fixture
    def axi_dispctrl_params(self, axi_dispctrl_module) -> dict:
        return axi_dispctrl_module.get_parameters()

    @pytest.fixture
    def axi_dispctrl_ports_by_dir(self, axi_dispctrl_module) -> dict:
        from fpga_topwrap.verilog_parser import group_ports_by_dir
        return group_ports_by_dir(axi_dispctrl_module.get_ports())


    def test_axi_dispctrl_parameters(self, axi_dispctrl_params):
        assert axi_dispctrl_params == {
            'C_S_AXIS_TDATA_WIDTH': 32,
            'C_S00_AXI_DATA_WIDTH': 32,
            'C_S00_AXI_ADDR_WIDTH': 7
        }


    def test_axi_dispctrl_ports(self, axi_dispctrl_ports_by_dir):
        assert axi_dispctrl_ports_by_dir['inout'] == []

        assert len(axi_dispctrl_ports_by_dir['in']) == 19
        assert {'name': 'S_AXIS_TDATA', 'bounds': ('(C_S_AXIS_TDATA_WIDTH-1)', '0')} in axi_dispctrl_ports_by_dir['in']
        assert {'name': 's00_axi_arprot', 'bounds': ('2', '0')} in axi_dispctrl_ports_by_dir['in']

        assert len(axi_dispctrl_ports_by_dir['out']) == 19
        assert {'name': 'DATA_O', 'bounds': ('(C_S_AXIS_TDATA_WIDTH-1)', '0')} in axi_dispctrl_ports_by_dir['out']
        assert {'name': 's00_axi_rresp', 'bounds': ('1', '0')} in axi_dispctrl_ports_by_dir['out']
