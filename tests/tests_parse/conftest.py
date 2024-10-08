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
def clog2_test_module() -> VerilogModule:
    from topwrap.verilog_parser import VerilogModuleGenerator

    verilog_modules = VerilogModuleGenerator().get_modules(
        "tests/data/data_build/clog2/clog2_tester.v"
    )
    assert len(verilog_modules) == 1
    return verilog_modules[0]


@pytest.fixture
def dependant_verilog_module() -> VerilogModule:
    from tempfile import NamedTemporaryFile

    from topwrap.verilog_parser import VerilogModuleGenerator

    with NamedTemporaryFile("w", suffix=".v") as f:
        f.write(
            """
module module_deps;
    submodule1 sub1();

    generate
        if(1) begin
            genvar i;
            for(i = 0; i < 8; i += 1) begin
                genvar j;
                for(j = 0; j < 6; j += 1) begin
                    submodule2 sub2();
                end
            end

            submodule3 sub3();
        end
    endgenerate
endmodule
"""
        )
        f.flush()

        modules = VerilogModuleGenerator().get_modules(f.name)

    assert len(modules) == 1
    return modules[0]


@pytest.fixture
def axi_vhdl_module() -> VHDLModule:
    return VHDLModule("tests/data/data_parse/axi_dispctrl_v1_0.vhd")


@pytest.fixture
def seg7_4d_ctrl_modules() -> List[VerilogModule]:
    from topwrap.verilog_parser import VerilogModuleGenerator

    verilog_modules = VerilogModuleGenerator().get_modules("tests/data/data_parse/seg7_4d_ctrl.v")
    assert len(verilog_modules) == 9
    return verilog_modules
