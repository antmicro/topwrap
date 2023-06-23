# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

class TestHDLParse:
    def test_verilog_parse(self):
        from fpga_topwrap.verilog_parser import ipcore_desc_from_verilog_module, VerilogModuleGenerator
        from fpga_topwrap.interface_grouper import InterfaceGrouper
        verilog_modules = VerilogModuleGenerator().get_modules('tests/data/DMATop.v')
        iface_grouper = InterfaceGrouper(True, False, None)
        for module in verilog_modules:
            ipcore_desc_from_verilog_module(module, iface_grouper)

    def test_verilog_parse_iface_deduce(self):
        from fpga_topwrap.verilog_parser import ipcore_desc_from_verilog_module, VerilogModuleGenerator
        from fpga_topwrap.interface_grouper import InterfaceGrouper
        verilog_modules = VerilogModuleGenerator().get_modules('tests/data/DMATop.v')
        iface_grouper = InterfaceGrouper(False, True, None)
        for module in verilog_modules:
            ipcore_desc_from_verilog_module(module, iface_grouper)

    def test_vhdl_parse(self):
        from fpga_topwrap.vhdl_parser import ipcore_desc_from_vhdl_module, VHDLModule
        from fpga_topwrap.interface_grouper import InterfaceGrouper
        vhdl_module = VHDLModule('tests/data/axi_dispctrl_v1_0.vhd')
        iface_grouper = InterfaceGrouper(False, False, None)
        ipcore_desc_from_vhdl_module(vhdl_module, iface_grouper)

    def test_vhdl_parse_iface_deduce(self):
        from fpga_topwrap.vhdl_parser import ipcore_desc_from_vhdl_module, VHDLModule
        from fpga_topwrap.interface_grouper import InterfaceGrouper
        vhdl_module = VHDLModule('tests/data/axi_dispctrl_v1_0.vhd')
        iface_grouper = InterfaceGrouper(False, True, None)
        ipcore_desc_from_vhdl_module(vhdl_module, iface_grouper)
