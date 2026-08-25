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
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

from .test_ir_examples import TestIrExamples


class TestSystemVerilogSlangParser:
    def test_type_alias(self):
        front = SystemVerilogSlangParser()

        mod = """typedef logic[3:0] extreme_logic;
                 module inner(); typedef logic[1:0] weak_logic; endmodule"""
        [*_parsed] = front.parse_tree(ps.SyntaxTree.fromText(mod, front.src_man))
        typenames = {v.name for v in front._typedefs.values()}

        assert typenames == {"extreme_logic", "weak_logic"}

    def test_type_parameter(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc #(parameter type xyz, parameter type less = whocares)(input xyz a);
                     endmodule"""
        [mod], _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        assert mod.parameters == [
            Parameter(name="xyz"),
            Parameter(name="less", default_value=ElaboratableValue("whocares")),
        ]
        assert mod.ports == [Port(name="a", direction=PortDirection.IN, type=Bit())]

    def test_empty_parameter(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc #(, parameter X = 32)(input logic a);
                     endmodule"""
        [mod], _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        assert mod.parameters == [
            Parameter(name="X", default_value=ElaboratableValue("32")),
        ]
        assert mod.ports == [Port(name="a", direction=PortDirection.IN, type=Bit())]

    def test_unpacked(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc (output logic sigs[4]); endmodule"""
        [mod], _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        [port] = mod.ports
        assert isinstance(port.type, LogicArray)
        assert port.type.item == Bit() and port.type.dimensions[0] == Dimensions(
            lower=ElaboratableValue(4) - ElaboratableValue(1)
        )

    def test_enum_complex(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc(input enum logic[13:0] { A=3, B, C=8 } a; endmodule)"""
        [mod], _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        [port] = mod.ports
        assert isinstance(port.type, Enum)
        assert port.type.dimensions[0].upper == ElaboratableValue(13)
        assert port.type.variants["B"] == ElaboratableValue(3) + ElaboratableValue(1)
        assert port.type.variants["C"] == ElaboratableValue(8)


class TestSVFrontend:
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
        mods = {m.id.name: m for m in front.parse_str(sources).modules}

        intf = mods["advanced_top"].interfaces.find_by_name_or_error("SCI_ctrl")

        with pytest.MonkeyPatch().context() as ctx:
            # There isn't a way to parse nor represent missing signals in SV
            ctx.delitem(intf.signals, intf.definition.signals.find_by_name_or_error("wdata")._id)
            # Converting IR -> SV -> IR loses interface mode information
            ctx.setattr(intf, "mode", InterfaceMode.SUBORDINATE)
            validator(mods["advanced_top"])

    def test_existing_interface_definitions(self):
        front = SystemVerilogFrontend()
        mod_str = """interface AXI4Lite;
  logic AWREADY;
  logic WREADY;
  logic BVALID;
  logic ARREADY;
  logic RVALID;
  logic RDATA;
  logic AWVALID;
  logic AWADDR;
  logic WVALID;
  logic WDATA;
  logic BREADY;
  logic ARVALID;
  logic ARADDR;
  logic RREADY;
  logic BID;
  logic RID;
  logic BRESP;
  logic RRESP;
  logic AWID;
  logic ARID;
  logic WSTRB;
  logic AWPROT;
  logic ARPROT;

  modport manager(
    input AWREADY, WREADY, BVALID, ARREADY, RVALID, RDATA, BID, RID, BRESP, RRESP,
    output AWVALID, AWADDR, WVALID, WDATA, BREADY, ARVALID, ARADDR, RREADY, AWID, ARID,
    WSTRB, AWPROT, ARPROT
  );

  modport subordinate(
    output AWREADY, WREADY, BVALID, ARREADY, RVALID, RDATA, BID, RID, BRESP, RRESP,
    input AWVALID, AWADDR, WVALID, WDATA, BREADY, ARVALID, ARADDR, RREADY, AWID, ARID,
    WSTRB, AWPROT, ARPROT
  );

  modport unspecified(
    input AWREADY, WREADY, BVALID, ARREADY, RVALID, RDATA, BID, RID, BRESP, RRESP,
    output AWVALID, AWADDR, WVALID, WDATA, BREADY, ARVALID, ARADDR, RREADY, AWID, ARID,
    WSTRB, AWPROT, ARPROT
  );

endinterface"""
        out = front.parse_str([mod_str])
        assert len(out.interfaces) == 1
        assert out.interfaces[0].id.name == "AXI4Lite"

    def test_existing_name_conflict(self):
        existing_mod = Module(id=Identifier(name="name1"))
        front = SystemVerilogFrontend(modules=[existing_mod])

        out = front.parse_str(["module name1(); endmodule"])
        assert len(out.modules) == 1
        assert out.modules[0].id.name == "name1"

    def test_multiple_module_different_parameter(self):
        source = """
        module leaf(input logic i);
        endmodule

        module child #(parameter bit USE = 0)(input logic i);
            generate
                if (USE) begin : g
                    leaf l(.i(i));
                end
            endgenerate
        endmodule

        module top(input logic i);
            child #(.USE(0)) a(.i(i));
            child #(.USE(1)) b(.i(i));
        endmodule
        """

        out = SystemVerilogFrontend().parse_str([source])
        modules = {module.id.name: module for module in out.modules}

        assert set(modules) == {"top", "child"}

        top = modules["top"]
        child = modules["child"]

        assert top.design is not None
        assert len(top.design.components) == 2
        assert list(top.design.components)[0].module is child
        assert list(top.design.components)[1].module is child

        assert child.design is None
