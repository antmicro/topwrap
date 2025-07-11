# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import pytest
from pyslang import Compilation, DiagnosticEngine, SourceManager, SyntaxTree

from examples.ir_examples.modules import (
    adv_top,
    hier_top,
    intf_top,
    intr_top,
    simp_top,
)
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.backend.sv.common import serialize_select, serialize_type, sv_varname
from topwrap.backend.sv.design import _SystemVerilogDesignData
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    LogicArray,
    LogicBitSelect,
    LogicFieldSelect,
    LogicSelect,
    StructField,
)
from topwrap.model.misc import ElaboratableValue
from topwrap.model.module import Module


class SlangDiagnosticErrors(BaseException):
    def __init__(self, pretty_diags: str, *args: object) -> None:
        super().__init__(*args, f"The generated SV design contains errors:\n{pretty_diags}")


class TestSystemVerilogCommon:
    def test_varname(self):
        assert sv_varname("regular123") == "regular123"
        assert sv_varname("s  p a\nc e") == "s__p_a_c_e"
        assert sv_varname("123backme") == r"\123backme "
        assert sv_varname("123 s 'n b") == r"\123_s_'n_b "
        assert sv_varname(r"\already_done ") == r"\already_done "

    def test_serialize_type(self):
        assert serialize_type(Bit()) == "logic"
        assert (
            serialize_type(Bits(dimensions=[Dimensions(ElaboratableValue(34))])) == "logic [34:0]"
        )
        assert (
            serialize_type(Bits(dimensions=[Dimensions(ElaboratableValue(34))] * 3))
            == "logic [34:0][34:0][34:0]"
        )
        assert (
            serialize_type(
                BitStruct(
                    fields=[
                        StructField(name="a", type=Bit()),
                        StructField(
                            name="b", type=Bits(dimensions=[Dimensions(ElaboratableValue(15))])
                        ),
                        StructField(
                            name="122", type=BitStruct(fields=[StructField(name="i", type=Bit())])
                        ),
                    ]
                )
            )
            == """\
struct packed {
    logic a;
    logic [15:0] b;
    struct packed {
        logic i;
    } \\122 ;
}"""
        )

        assert serialize_type(BitStruct(name="axi_struct", fields=[])) == "axi_struct"
        assert (
            serialize_type(BitStruct(fields=[]))
            == "struct packed {\n\n}"
            == serialize_type(BitStruct(name="axi_struct", fields=[]), tld=True)
        )


class TestSystemVerilogDesignBackend:
    @pytest.fixture
    def svdb(self) -> _SystemVerilogDesignData:
        return _SystemVerilogDesignData()

    @pytest.fixture
    def adv_des(self) -> Design:
        assert adv_top.design is not None
        return adv_top.design

    def test_ser_select(self):
        logic = LogicArray(
            item=BitStruct(
                fields=[
                    StructField(
                        name="uhuhu",
                        type=Bits(
                            dimensions=[
                                Dimensions(ElaboratableValue(7)),
                                Dimensions(ElaboratableValue(31)),
                            ]
                        ),
                    )
                ]
            ),
            dimensions=[Dimensions(ElaboratableValue(3))],
        )

        out = serialize_select(
            LogicSelect(
                logic=logic,
                ops=[
                    LogicBitSelect(Dimensions.single(ElaboratableValue(2))),
                    LogicFieldSelect(logic.item.fields[0]),
                    LogicBitSelect(Dimensions(ElaboratableValue(30), ElaboratableValue(20))),
                ],
            )
        )

        assert out == "[2:2].uhuhu[30:20]"

    def test_plain_const_conn(self, svdb: _SystemVerilogDesignData):
        assert intf_top.design is not None

        const_con = intf_top.design.connections.find_by(lambda c: isinstance(c, ConstantConnection))
        assert isinstance(const_con, ConstantConnection)
        svdb.parse_connection(const_con)
        svdb.parse_partial_conns()

        assert const_con.target.instance is not None
        assert svdb.port_maps == {
            const_con.target.instance._id: {const_con.target.io.name: const_con.source.value}
        }

    def test_plain_port_conn(self, svdb: _SystemVerilogDesignData, adv_des: Design):
        conn = adv_des.connections.find_by(
            lambda c: isinstance(c, PortConnection) and c.source.io.name == "byte"
        )
        assert isinstance(conn, PortConnection)

        svdb.parse_connection(conn)
        svdb.parse_partial_conns()

        assert conn.target.instance is not None
        assert svdb.port_maps == {conn.target.instance._id: {"byte": f"sseq.{sv_varname('byte')}"}}

    def test_external_const_conn(self, svdb: _SystemVerilogDesignData, adv_des: Design):
        conn = adv_des.connections[0]
        assert isinstance(conn, ConstantConnection)

        svdb.parse_connection(conn)
        svdb.parse_partial_conns()

        assert svdb.assign_map[conn.target.io.name] == conn.source.value

    def test_external_port_conn(self, svdb: _SystemVerilogDesignData, adv_des: Design):
        ext_in = adv_des.connections.find_by(lambda c: c.target.io.name == "clk")
        assert isinstance(ext_in, PortConnection)
        assert intf_top.design is not None
        ext_inout = intf_top.design.connections.find_by(lambda c: c.target.io.name == "ext")
        assert isinstance(ext_inout, PortConnection)
        ext_out = adv_des.connections.find_by(
            lambda c: isinstance(c, PortConnection)
            and c.target
            == ReferencedPort.external(adv_des.parent.ports.find_by_name_or_error("cow_out"))
        )
        assert isinstance(ext_out, PortConnection)

        svdb.parse_connection(ext_in)
        svdb.parse_connection(ext_out)
        svdb.parse_connection(ext_inout)
        svdb.parse_partial_conns()

        assert ext_inout.source.instance is not None
        assert ext_in.target.instance is not None
        assert svdb.port_maps == {
            ext_in.target.instance._id: {ext_in.target.io.name: ext_in.source.io.name},
            ext_inout.source.instance._id: {ext_inout.source.io.name: ext_inout.target.io.name},
        }
        assert ext_out.source.instance is not None
        assert svdb.assign_map == {
            ext_out.target.io.name: f"{ext_out.source.instance.name}.{ext_out.source.io.name}"
            f"{serialize_select(ext_out.source.select)}"
        }

    def test_net_creation(self, svdb: _SystemVerilogDesignData, adv_des: Design):
        half1 = adv_des.connections[1]
        assert isinstance(half1, PortConnection)
        half2 = adv_des.connections[2]
        assert isinstance(half2, PortConnection)

        svdb.parse_connection(half1)
        svdb.parse_connection(half2)
        svdb.parse_partial_conns()

        assert half1.target.instance is not None
        assert half1.target.instance is half2.target.instance
        assert half1.target.io is half2.target.io
        net_name = f"{half1.target.instance.name}__{half1.target.io.name}"

        assert svdb.nets == {net_name: half1.target.io.type}
        assert svdb.port_maps == {half1.target.instance._id: {half1.target.io.name: net_name}}
        assert svdb.assign_map == {
            f"{net_name}{serialize_select(half1.target.select)}": f"{half1.source.io.name}"
            f"{serialize_select(half1.source.select)}",
            f"{net_name}{serialize_select(half2.target.select)}": f"{half2.source.io.name}"
            f"{serialize_select(half2.source.select)}",
        }

    @pytest.fixture
    def svdb_and_cons(
        self, svdb: _SystemVerilogDesignData, adv_des: Design
    ) -> tuple[_SystemVerilogDesignData, InterfaceConnection, InterfaceConnection]:
        int_con = adv_des.connections.find_by(lambda c: c.target.io.name == "SCI")
        assert isinstance(int_con, InterfaceConnection)
        ext_con = adv_des.connections.find_by(
            lambda c: c.target.io.name == "externally_controlled_SCI"
        )
        assert isinstance(ext_con, InterfaceConnection)

        svdb.parse_connection(int_con)
        svdb.parse_connection(ext_con)
        svdb.parse_partial_conns()

        return svdb, int_con, ext_con

    def test_intf_independent_signals(
        self,
        svdb_and_cons: tuple[_SystemVerilogDesignData, InterfaceConnection, InterfaceConnection],
    ):
        svdb, int_con, ext_con = svdb_and_cons

        # internal part
        cs, ct = int_con.source, int_con.target
        assert cs.instance is not None and ct.instance is not None
        intf_name = f"{cs.instance.name}__{cs.io.name}__{ct.instance.name}__{ct.io.name}"
        assert svdb.intf_decls == {intf_name: int_con.source.io.definition}
        assert svdb.port_maps[cs.instance._id][cs.io.name] == intf_name
        assert svdb.port_maps[ct.instance._id][ct.io.name] == intf_name

        # external part
        assert ext_con.target.instance is not None
        assert (
            svdb.port_maps[ext_con.target.instance._id][ext_con.target.io.name]
            == ext_con.source.io.name
        )

    def test_intf_sliced_signals(
        self,
        svdb_and_cons: tuple[_SystemVerilogDesignData, InterfaceConnection, InterfaceConnection],
    ):
        svdb, int_con, ext_con = svdb_and_cons

        # internal part
        cs, ct = int_con.source, int_con.target
        assert cs.instance is not None and ct.instance is not None
        intf_name = f"{cs.instance.name}__{cs.io.name}__{ct.instance.name}__{ct.io.name}"
        net_name = f"{ct.instance.name}__sci_control"
        assert svdb.intf_decls == {intf_name: int_con.source.io.definition}
        assert svdb.nets == {net_name: ct.io.parent.ports.find_by_name_or_error("sci_control").type}
        assert svdb.port_maps[ct.instance._id]["sci_control"] == net_name
        for sig in ("addr", "write", "strb", "ack"):
            assert svdb.assign_map[f"{intf_name}.{sig}"] == f"{net_name}.{sig}"
        assert len(svdb.assign_map) == 4

        # external part
        cs, ct = ext_con.source, ext_con.target
        assert ct.instance is not None and cs.instance is None
        assert svdb.port_maps[ct.instance._id][ct.io.name] == cs.io.name
        assert svdb.port_maps[ct.instance._id]["plain_ack"] == f"{cs.io.name}.ack"
        assert svdb.port_maps[ct.instance._id]["plain_sack"] == f"{cs.io.name}.sack"

    def test_intf_default_value(
        self,
        svdb_and_cons: tuple[_SystemVerilogDesignData, InterfaceConnection, InterfaceConnection],
    ):
        svdb, _, ext_con = svdb_and_cons

        assert ext_con.target.instance is not None
        proc_mod = ext_con.target.instance.module
        esci = proc_mod.interfaces.find_by_name_or_error("externally_controlled_SCI")
        sig = esci.definition.signals.find_by_name_or_error("wdata")
        assert sig.default is not None
        slice = ReferencedPort.external(proc_mod.ports.find_by_name_or_error("plain_wdata"))
        assert esci.signals[sig._id] == slice
        assert svdb.port_maps[ext_con.target.instance._id][slice.io.name] == sig.default.value

    def test_intf_both_external(self, svdb: _SystemVerilogDesignData, adv_des: Design):
        conn = adv_des.connections.find_by(
            lambda c: isinstance(c, InterfaceConnection)
            and c.target.is_external
            and c.source.is_external
        )
        assert isinstance(conn, InterfaceConnection)

        svdb.handle_intf_con(conn)

        for sig in conn.source.io.definition.signals:
            src = f"{sv_varname(conn.source.io.name)}.{sv_varname(sig.name)}"
            trg = f"{sv_varname(conn.target.io.name)}.{sv_varname(sig.name)}"
            if sig.modes[conn.source.io.mode].direction is PortDirection.IN:
                assert svdb.assign_map[trg] == src
            else:
                assert svdb.assign_map[src] == trg


class TestSystemVerilogBackend:
    def test_repr_empty_package(self):
        back = SystemVerilogBackend(desc_comms=False)

        assert back.represent_package("packpack", {}).content == "package packpack;\nendpackage\n"

    def test_repr_package(self):
        back = SystemVerilogBackend(desc_comms=False)

        assert adv_top.design is not None
        cow = (
            adv_top.design.components.find_by_name_or_error("proc")
            .module.ports.find_by_name_or_error("cows")
            .type
        )
        strs = adv_top.ports.find_by_name_or_error("char_streams").type
        assert isinstance(cow, BitStruct) and isinstance(strs, BitStruct)
        assert cow.name is not None and strs.name is not None

        out = back.represent_package(
            "advanced_top_pkg",
            {
                strs.name: strs,
                cow.name: cow,
            },
        ).content

        assert (
            out
            == """package advanced_top_pkg;
    typedef struct packed {
        logic [7:0] enc;
        logic [31:0] length;
    } cow_struct;

    typedef struct packed {
        logic [63:0][7:0] a_stream;
        logic [63:0][7:0] b_stream;
    } stream_struct;

endpackage
"""
        )

    def test_repr_intf(self):
        back = SystemVerilogBackend(desc_comms=False)

        assert intf_top.design is not None
        comp = intf_top.design.components.find_by_name_or_error("receiver").module.interfaces[0]
        out = back.represent_interface(comp.definition).content

        assert (
            out
            == """interface AXI_4_Stream;
  logic TVALID;
  logic TREADY;
  logic TDATA;
  logic TKEEP;

  modport manager(
    output TVALID, TDATA, TKEEP,
    input TREADY
  );

  modport subordinate(
    input TVALID, TDATA, TKEEP,
    output TREADY
  );

endinterface
"""
        )

    def test_combined_repr(self):
        back = SystemVerilogBackend(desc_comms=False)
        out = back.represent(adv_top)

        assert out.base_name == adv_top.id.name
        assert out.package is not None
        assert out.interfaces == [
            back.represent_interface(adv_top.interfaces[0].definition, out.package.name)
        ]
        assert len(out.modules) == 1
        assert len([*back.serialize(out, combine=True)]) == 1
        assert len([*back.serialize(out)]) == 3

    @pytest.mark.parametrize("module", (simp_top, hier_top, intf_top, intr_top, adv_top))
    def test_generated_syntax(self, module: Module):
        back = SystemVerilogBackend(all_pins=True, desc_comms=True, mod_stubs=True)
        [out] = back.serialize(back.represent(module), combine=True)

        srcman = SourceManager()
        tree = SyntaxTree.fromText(out.content, srcman, name=out.filename)
        deng = DiagnosticEngine(srcman)
        comp = Compilation()
        comp.addSyntaxTree(tree)
        ediags = [d for d in comp.getAllDiagnostics() if d.isError()]
        pretty_diags = deng.reportAll(srcman, ediags)

        if ediags != []:
            raise SlangDiagnosticErrors(pretty_diags)
