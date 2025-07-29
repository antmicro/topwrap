# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from typing import Callable

import pyslang as ps
import pytest

from examples.ir_examples.advanced.ir.types import sci_intf
from examples.ir_examples.modules import adv_top
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.frontend.frontend import FrontendParseStrInput
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.sv.module import SystemVerilogSlangParser
from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bit, Dimensions, Enum, LogicArray
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import ElaboratableValue, Parameter
from topwrap.model.module import Module

from .test_ir_examples import TestIrExamples


class TestSystemVerilogSlangParser:
    def test_type_alias(self):
        front = SystemVerilogSlangParser()

        mod = """typedef logic[3:0] extreme_logic;
                 module inner(); typedef logic[1:0] weak_logic; endmodule"""
        [*_parsed] = front.parse_tree(ps.SyntaxTree.fromText(mod))
        typenames = {v.name for v in front._typedefs.values()}

        assert typenames == {"extreme_logic", "weak_logic"}

    def test_type_parameter(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc #(parameter type xyz, parameter type less = whocares)(input xyz a);
                     endmodule"""
        [mod] = front.parse_tree(ps.SyntaxTree.fromText(mod_str))
        assert mod.parameters == [
            Parameter(name="xyz"),
            Parameter(name="less", default_value=ElaboratableValue("whocares")),
        ]
        assert mod.ports == [Port(name="a", direction=PortDirection.IN, type=Bit())]

    def test_unpacked(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc (output logic sigs[4]); endmodule"""
        [mod] = front.parse_tree(ps.SyntaxTree.fromText(mod_str))
        [port] = mod.ports
        assert isinstance(port.type, LogicArray)
        assert port.type.item == Bit() and port.type.dimensions[0] == Dimensions(
            lower=ElaboratableValue(4) - ElaboratableValue(1)
        )

    def test_enum_complex(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc(input enum logic[13:0] { A=3, B, C=8 } a; endmodule)"""
        [mod] = front.parse_tree(ps.SyntaxTree.fromText(mod_str))
        [port] = mod.ports
        assert isinstance(port.type, Enum)
        assert port.type.dimensions[0].upper == ElaboratableValue(13)
        assert port.type.variants["B"] == ElaboratableValue(3) + ElaboratableValue(1)
        assert port.type.variants["C"] == ElaboratableValue(8)

    @pytest.mark.parametrize(
        ["mod", "validator"],
        [
            # (simp_top, TestIrExamples.ir_simple),
            # (hier_top, TestIrExamples.ir_hierarchy),
            # (intf_top, TestIrExamples.ir_interface),
            # (intr_top, TestIrExamples.ir_interconnect),
            # Other IR examples make no sense to be tested
            # without a working Design frontend
            (adv_top, TestIrExamples.ir_advanced)
        ],
    )
    def test_ir_examples(self, mod: Module, validator: Callable[[Module], None]):
        back = SystemVerilogBackend(all_pins=True, desc_comms=True, mod_stubs=True)
        sources = (
            FrontendParseStrInput(o.filename, o.content)
            for o in back.serialize(back.represent(mod))
        )

        front = SystemVerilogFrontend(interfaces=[sci_intf])
        mods = {m.id.name: m for m in front.parse_str(sources)}

        intf = mods["advanced_top"].interfaces.find_by_name_or_error("SCI_ctrl")

        with pytest.MonkeyPatch().context() as ctx:
            # There isn't a way to parse nor represent missing signals in SV
            ctx.delitem(intf.signals, intf.definition.signals.find_by_name_or_error("wdata")._id)
            # Converting IR -> SV -> IR loses interface mode information
            ctx.setattr(intf, "mode", InterfaceMode.SUBORDINATE)
            validator(mods["advanced_top"])
