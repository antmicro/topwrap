# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from typing import List

import pytest

from topwrap.verilog_parser import VerilogModule
from topwrap.vhdl_parser import VHDLModule


@pytest.fixture
def axi_verilog_module() -> VerilogModule:
    from topwrap.verilog_parser import VerilogModuleGenerator

    verilog_modules = VerilogModuleGenerator().get_modules(
        "tests/data/data_parse/axi_axil_adapter.v"
    )
    assert len(verilog_modules) == 1
    return verilog_modules[0]


@pytest.fixture
def axi_vhdl_module() -> VHDLModule:
    return VHDLModule("tests/data/data_parse/axi_dispctrl_v1_0.vhd")


@pytest.fixture
def seg7_4d_ctrl_modules() -> List[VerilogModule]:
    from topwrap.verilog_parser import VerilogModuleGenerator

    verilog_modules = VerilogModuleGenerator().get_modules("tests/data/data_parse/seg7_4d_ctrl.v")
    assert len(verilog_modules) == 9
    return verilog_modules
