# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Callable

import pyslang as ps
import pytest

from examples.ir_examples.advanced.ir.types import sci_intf
from examples.ir_examples.modules import adv_top
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.frontend.frontend import (
    FrontendApproach,
    FrontendParseException,
    FrontendParseStrInput,
)
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.sv.module import SystemVerilogSlangParser
from topwrap.model.connections import ConstantConnection, Port, PortDirection
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
        [mod], _, _, _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        assert mod.parameters == [
            Parameter(name="xyz"),
            Parameter(name="less", default_value=ElaboratableValue("whocares")),
        ]
        assert mod.ports == [Port(name="a", direction=PortDirection.IN, type=Bit())]

    def test_empty_parameter(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc #(, parameter X = 32)(input logic a);
                     endmodule"""
        [mod], _, _, _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        assert mod.parameters == [
            Parameter(name="X", default_value=ElaboratableValue("32")),
        ]
        assert mod.ports == [Port(name="a", direction=PortDirection.IN, type=Bit())]

    def test_unpacked(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc (output logic sigs[4]); endmodule"""
        [mod], _, _, _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        [port] = mod.ports
        assert isinstance(port.type, LogicArray)
        assert port.type.item == Bit() and port.type.dimensions[0] == Dimensions(
            lower=ElaboratableValue(4) - ElaboratableValue(1)
        )

    def test_enum_complex(self):
        front = SystemVerilogSlangParser()
        mod_str = """module abc(input enum logic[13:0] { A=3, B, C=8 } a); endmodule"""
        [mod], _, _, _ = front.parse_tree(ps.SyntaxTree.fromText(mod_str, front.src_man))
        [port] = mod.ports
        assert isinstance(port.type, Enum)
        assert port.type.dimensions[0].upper == ElaboratableValue(13)
        assert port.type.variants["B"] == ElaboratableValue(3) + ElaboratableValue(1)
        assert port.type.variants["C"] == ElaboratableValue(8)


class TestSVFrontend:
    def test_wide_constant_connection_keeps_full_precision(self):
        value = 2**400 + 7
        source = f"""
        module child(input logic [511:0] i);
        endmodule

        module top;
            child u(.i(512'd{value}));
        endmodule
        """

        parsed = SystemVerilogFrontend().parse_str([source])
        top = next(module for module in parsed.modules if module.id.name == "top")

        assert top.design is not None
        [connection] = [
            connection
            for connection in top.design.connections
            if isinstance(connection, ConstantConnection)
        ]
        assert connection.source.value == f"512'd{value}"
        assert "..." not in connection.source.value

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

    def test_parse_valid_module(self):
        parsed = SystemVerilogFrontend().parse_str(
            [
                """
module simple_module(
    input logic clk,
    output logic data
);
endmodule
"""
            ]
        )

        [module] = parsed.modules
        assert module.id.name == "simple_module"
        assert [port.name for port in module.ports] == ["clk", "data"]

    def test_parse_files(self, tmp_path: Path):
        source = tmp_path / "simple_module.sv"
        source.write_text("""
module simple_module(
    input logic clk,
    output logic data
);
endmodule
""")

        parsed = SystemVerilogFrontend().parse_files([source])

        [module] = parsed.modules
        assert module.id.name == "simple_module"

    def test_invalid_syntax_in_body(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FrontendParseException, match="expected"):
                SystemVerilogFrontend().parse_str(
                    [
                        """module simple_module(
    input logic clk,
    output logic data
);
assign data = 1
endmodule
"""
                    ]
                )

    def test_syntax_errors_are_reported_as_errors(self, caplog: pytest.LogCaptureFixture):
        invalid_source = """
        module broken_module(
            this is not a valid port declaration;
        );
        endmodule
        """

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FrontendParseException, match="expected"):
                SystemVerilogFrontend().parse_str([invalid_source])

    def test_expected_expression_in_module_body_is_an_error(self):
        source = """
        module top(output logic data);
            assign data = ;
        endmodule
        """

        with pytest.raises(FrontendParseException, match="expected expression"):
            SystemVerilogFrontend().parse_str([source])

    def test_expected_declarator_in_module_body_is_an_error(self):
        source = """
        module top;
            logic ;
        endmodule
        """

        with pytest.raises(FrontendParseException, match="expected a declaration name"):
            SystemVerilogFrontend().parse_str([source])

    def test_undeclared_identifier_in_assignment_is_an_error(self):
        source = """
        module top(output logic data);
            assign data = missing_signal;
        endmodule
        """

        with pytest.raises(FrontendParseException, match="undeclared identifier"):
            SystemVerilogFrontend().parse_str([source])

    def test_missing_module_is_an_error_in_strict_mode(self):
        incomplete_source = """
        module top(input logic clk);
            missing_module u_missing(.clk(clk));
        endmodule
        """

        with pytest.raises(FrontendParseException, match="unknown module 'missing_module'"):
            SystemVerilogFrontend().parse_str([incomplete_source])

    def test_predefined_module_instance_is_not_an_error_in_strict_mode(self):
        [sub] = (
            SystemVerilogFrontend().parse_str(["module sub(input logic clk); endmodule"]).modules
        )

        modules = (
            SystemVerilogFrontend(modules=[sub])
            .parse_str(["module top(input logic clk); sub u_sub(.clk(clk)); endmodule"])
            .modules
        )

        assert [m.id.name for m in modules] == ["top"]

    def test_multiple_unknown_modules_are_reported_in_best_effort_errors(
        self, caplog: pytest.LogCaptureFixture
    ):
        incomplete_source = """
        module top;
            unknown_a a();
            unknown_b b();
        endmodule
        """

        with caplog.at_level(logging.ERROR):
            SystemVerilogFrontend(approach=FrontendApproach.BEST_EFFORT).parse_str(
                [incomplete_source]
            )

        error_records = [
            record
            for record in caplog.records
            if record.name == "topwrap.frontend.sv.frontend" and record.levelno >= logging.ERROR
        ]
        assert len(error_records) == 2
        assert "unknown module 'unknown_a'" in error_records[0].message
        assert "unknown module 'unknown_b'" in error_records[1].message

    def test_header_warning_is_nonfatal_in_strict_mode(self, caplog: pytest.LogCaptureFixture):
        source = "module top #(parameter X = 4'd32)(); endmodule"

        with caplog.at_level(logging.WARNING):
            parsed = SystemVerilogFrontend().parse_str([source])

        assert [module.id.name for module in parsed.modules] == ["top"]
        assert any(
            record.levelno == logging.WARNING and "vector-overflow" in record.message
            for record in caplog.records
        )

    def test_macro_expansion_in_header_is_reported_as_warning(
        self, caplog: pytest.LogCaptureFixture
    ):
        source = """
        `define WIDTH missing
        module top(input logic [`WIDTH-1:0] a);
        endmodule
        """

        with caplog.at_level(logging.WARNING):
            parsed = SystemVerilogFrontend().parse_str([source])

        [module] = parsed.modules
        assert module.id.name == "top"
        assert [port.name for port in module.ports] == ["a"]
        assert any(
            record.levelno == logging.WARNING
            and "undeclared identifier 'missing'" in record.message
            for record in caplog.records
        )

    def test_unknown_macro_in_module_body_is_ignored(self, caplog: pytest.LogCaptureFixture):
        source = """
        module top;
            `UNKNOWN_MACRO(argument)
        endmodule
        """

        with caplog.at_level(logging.WARNING):
            parsed = SystemVerilogFrontend().parse_str([source])

        assert [module.id.name for module in parsed.modules] == ["top"]
        assert "UNKNOWN_MACRO" not in caplog.text

    def test_unknown_macro_in_module_header_is_an_error(self):
        source = """
        module top(
            `UNKNOWN_MACRO(argument)
        );
        endmodule
        """

        with pytest.raises(FrontendParseException, match="unknown macro"):
            SystemVerilogFrontend().parse_str([source])

    def test_missing_include_is_reported_as_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ):
        source = tmp_path / "missing_include.sv"
        source.write_text('`include "does_not_exist.svh"\nmodule top; endmodule\n')

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FrontendParseException):
                SystemVerilogFrontend().parse_files([source])

    def test_best_effort_recovers_modules_after_syntax_error(
        self, caplog: pytest.LogCaptureFixture
    ):
        source = """
        module broken_module(
            this is not a valid port declaration;
        );
        endmodule

        module good_module(input logic clk, output logic data);
        endmodule
        """

        with caplog.at_level(logging.ERROR):
            parsed = SystemVerilogFrontend(approach=FrontendApproach.BEST_EFFORT).parse_str(
                [source]
            )

        modules = {module.id.name: module for module in parsed.modules}
        assert set(modules) == {"broken_module", "good_module"}
        assert len(modules["broken_module"].ports) == 0
        assert [port.name for port in modules["good_module"].ports] == ["clk", "data"]
        assert modules["broken_module"].design is None
        assert modules["good_module"].design is None
        assert any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_best_effort_keeps_ir_for_unknown_instance(self, caplog: pytest.LogCaptureFixture):
        source = """
        module top(input logic clk);
            missing_module u_missing(.clk(clk));
        endmodule
        """

        with caplog.at_level(logging.ERROR):
            parsed = SystemVerilogFrontend(approach=FrontendApproach.BEST_EFFORT).parse_str(
                [source]
            )

        [module] = parsed.modules
        assert module.id.name == "top"
        assert [port.name for port in module.ports] == ["clk"]
        assert module.design is None
        assert "unknown module 'missing_module'" in caplog.text
        assert any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_best_effort_returns_recovered_ir_from_invalid_header(
        self, caplog: pytest.LogCaptureFixture
    ):
        source = """
        module broken_module(
            this is not a valid port declaration;
        );
        endmodule
        """

        with caplog.at_level(logging.ERROR):
            parsed = SystemVerilogFrontend(approach=FrontendApproach.BEST_EFFORT).parse_str(
                [source]
            )

        [module] = parsed.modules
        assert module.id.name == "broken_module"
        assert len(module.ports) == 0
        assert module.design is None
        assert any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_best_effort_keeps_ir_after_missing_include(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ):
        source = tmp_path / "top.sv"
        source.write_text(
            '`include "does_not_exist.svh"\n'
            "module top(input logic clk, output logic data); endmodule\n"
        )

        with caplog.at_level(logging.ERROR):
            parsed = SystemVerilogFrontend(approach=FrontendApproach.BEST_EFFORT).parse_files(
                [source]
            )

        [module] = parsed.modules
        assert module.id.name == "top"
        assert [port.name for port in module.ports] == ["clk", "data"]
        assert module.design is None
        assert "No such file or directory" in caplog.text
        assert any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_parse_multiple_sources(self):
        parsed = SystemVerilogFrontend().parse_str(
            [
                "module first; endmodule",
                "module second; endmodule",
            ]
        )

        assert {module.id.name for module in parsed.modules} == {"first", "second"}

    def test_parse_interface(self):
        source = """
        interface simple_if;
            logic data;
        endinterface
        """

        parsed = SystemVerilogFrontend().parse_str([source])

        assert [interface.id.name for interface in parsed.interfaces] == ["simple_if"]
