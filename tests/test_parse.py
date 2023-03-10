# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

class TestHDLParse:
    def test_verilog_parse(self):
        from fpga_topwrap.verilog_parser import ipcore_desc_from_verilog
        ipcore_desc_from_verilog('tests/data/DMATop.v', None, False)

    def test_verilog_parse_iface_deduce(self):
        from fpga_topwrap.verilog_parser import ipcore_desc_from_verilog
        ipcore_desc_from_verilog('tests/data/DMATop.v', None, True)

    def test_vhdl_parse(self):
        from fpga_topwrap.vhdl_parser import ipcore_desc_from_vhdl
        ipcore_desc_from_vhdl('tests/data/axi_dispctrl_v1_0.vhd', None, False)

    def test_vhdl_parse_iface_deduce(self):
        from fpga_topwrap.vhdl_parser import ipcore_desc_from_vhdl
        ipcore_desc_from_vhdl('tests/data/axi_dispctrl_v1_0.vhd', None, True)
