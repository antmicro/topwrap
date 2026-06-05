# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Union

import pytest

from examples.ir_examples.advanced.ir.types import sci_intf
from examples.ir_examples.modules import (
    adv_top,
    clk_top,
    hier_top,
    intf_top,
    intr_top,
    inv_adder,
    inv_crg,
    inv_top,
    lfsr_gen,
    proc_mod,
    seq_sci_mod,
    simp_top,
    sseq_mod,
    two_mux,
)
from topwrap.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRFeature,
    WishboneRRParams,
)
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
    ResetPolarity,
)
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    Enum,
    LogicArray,
    StructField,
)
from topwrap.model.interface import InterfaceMode, InterfaceSignalConfiguration
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module


class TestIrExamples:
    """
    Tests based on IR examples for frontends that verify whether
    a top-level Module parsed by them matches up with the original
    Module as defined in the examples directory.

    Also does a basic smoke test on the definitions themselves.
    """

    @staticmethod
    def ir_simple(mod: Module):
        assert mod.id == Identifier(name="simp_top")

        ports = [(p.name, p.direction) for p in mod.ports]
        assert all(
            n in ports
            for n in (
                ("clk", PortDirection.IN),
                ("rst", PortDirection.IN),
                ("sel_gen", PortDirection.IN),
                ("rnd_bit", PortDirection.OUT),
            )
        )
        assert len(mod.interfaces) == 0

        assert mod.design is not None
        components = [c.name for c in mod.design.components]
        assert all(n in components for n in ["gen2", "2mux", "gen1"])

        gen1 = mod.design.components.find_by_name_or_error("gen1")
        mux2 = mod.design.components.find_by_name_or_error("2mux")
        assert gen1.module is lfsr_gen
        assert mux2.module is two_mux

        param = next(v for p, v in gen1.parameters.items() if p.resolve().name == "SEED")
        assert param.value == "1337"

        assert len(mod.design.connections) == 8
        assert (
            len(
                [
                    c
                    for c in mod.design.connections
                    if not c.source.is_external and not c.target.is_external
                ]
            )
            == 2
        )

    @staticmethod
    def ir_interface(mod: Module):
        assert mod.design is not None

        const = next(c for c in mod.design.connections if isinstance(c, ConstantConnection))
        intf = next(c for c in mod.design.connections if isinstance(c, InterfaceConnection))
        assert const.source.value == "2888"

        if intf.source.instance.name == "streamer":
            source = intf.source
            target = intf.target
        else:
            source = intf.target
            target = intf.source

        assert source.instance.name == "streamer"
        assert target.instance.name == "receiver"
        assert (defi := target.io.definition) is source.io.definition
        assert defi.id.name == "AXI 4 Stream"
        assert source.io.mode == InterfaceMode.MANAGER
        assert target.io.mode == InterfaceMode.SUBORDINATE
        tvalid = next(s for s in defi.signals if s.name == "TVALID")
        assert source.io.signals[tvalid._id].io.name == "ctrl_o"

        assert len(target.instance.module.ports) == 6
        ctrl_i = target.instance.module.ports.find_by_name("ctrl_i").type
        assert isinstance(ctrl_i, Bits)
        assert ctrl_i.dimensions[0].upper == ElaboratableValue(4)
        assert ctrl_i.dimensions[0].lower == ElaboratableValue(0)
        signal = target.io.signals[defi.signals.find_by_name("TVALID")._id]
        assert signal.io.type == ctrl_i
        assert signal.select.ops[0].slice == Dimensions(
            upper=ElaboratableValue(4), lower=ElaboratableValue(4)
        )

    @staticmethod
    def ir_hierarchy(mod: Module):
        assert mod.design is not None

        subdes = mod.design.components[0].module.design
        assert subdes is not None
        assert subdes.parent.id.name == "proc"
        assert len(subdes.parent.ports) == 6

        bitcnt = next(c for c in subdes.components if c.name == "4-bit counter")
        assert len(bitcnt.module.ports) == 3
        assert bitcnt.module.design is not None
        assert len(bitcnt.module.design.components) == 2

    @staticmethod
    def ir_interconnect(mod: Module):
        assert mod.design is not None

        [intr] = mod.design.interconnects
        assert intr.clock.io.name == "clk"
        assert intr.reset.io.name == "rst"
        assert isinstance(intr, WishboneInterconnect)

        assert isinstance(intr.params, WishboneRRParams)
        assert intr.params.addr_width.value == "32"
        assert intr.params.data_width.value == "8"
        assert intr.params.granularity == 8
        assert intr.params.features == {WishboneRRFeature.ERR, WishboneRRFeature.STALL}

        assert len(intr.managers) == 2
        assert len(intr.subordinates) == 2
        cpu, ext = [m.resolve() for m in intr.managers]
        assert cpu.instance.name == "cpu"
        assert ext.is_external or ext.instance.name == "wb_pass"
        dsp, mem = intr.subordinates.items()
        assert dsp[0].resolve().instance.name == "dsp"

        assert mem[1].address.value == "65536"
        assert mem[1].size.value == "255"

    @staticmethod
    def ir_advanced(mod: Module):
        # Top level
        assert mod.id.name == "advanced_top"
        assert len(mod.parameters) == 2
        assert (
            Parameter(name="CIF_ADDR_WIDTH", default_value=ElaboratableValue(32)) in mod.parameters
        )
        assert (
            Parameter(name="CIF_DATA_WIDTH", default_value=ElaboratableValue(64)) in mod.parameters
        )

        assert len(mod.ports) == 4
        for n in ["char_streams", "cow_out", "hw_id", "clk"]:
            assert mod.ports.find_by_name(n)
        assert isinstance(cstr := mod.ports.find_by_name_or_error("char_streams").type, BitStruct)
        assert isinstance(mod.ports.find_by_name_or_error("hw_id").type, LogicArray)
        assert isinstance(mod.ports.find_by_name_or_error("clk").type, Bit)

        mode = next(f for f in cstr.fields if f.field_name == "transfer_mode")
        assert mode.type == Enum(
            dimensions=[Dimensions(ElaboratableValue(7))],
            variants={
                "SIMPLE": ElaboratableValue(0x53),
                "COMPLEX": ElaboratableValue(0x54),
                "WHOLEHEARTED": ElaboratableValue(0x55),
            },
        )

        assert len(mod.interfaces) == 3
        intf = mod.interfaces[0]
        assert intf.name == "SCI_ctrl"
        assert intf.mode == InterfaceMode.SUBORDINATE
        assert not intf.has_sliced_signals
        assert intf.has_independent_signals

        # SCI interface
        idef = intf.definition
        assert idef.id.name == "Simply Complex Interface 4"
        addr = idef.signals.find_by_name_or_error("addr")
        assert addr._id in intf.signals
        assert addr.type == Bits(dimensions=[Dimensions(ElaboratableValue("32-1"))])
        assert addr.modes[InterfaceMode.MANAGER] == InterfaceSignalConfiguration(
            PortDirection.OUT, True
        )
        assert addr.modes[InterfaceMode.SUBORDINATE] == InterfaceSignalConfiguration(
            PortDirection.IN, True
        )
        rdata = idef.signals.find_by_name_or_error("rdata")
        assert addr._id in intf.signals
        assert rdata.type == Bits(dimensions=[Dimensions(ElaboratableValue("64-1"))])
        assert rdata.modes[InterfaceMode.MANAGER] == InterfaceSignalConfiguration(
            PortDirection.IN, True
        )
        assert rdata.modes[InterfaceMode.SUBORDINATE] == InterfaceSignalConfiguration(
            PortDirection.OUT, False
        )
        assert rdata.default == ElaboratableValue(0)
        assert idef.signals.find_by_name_or_error("wdata")._id not in intf.signals
        assert idef is sci_intf

        # string_sequencer
        assert sseq_mod.id.name == "string_sequencer"
        assert len(sseq_mod.ports) == 3
        assert sseq_mod.ports.find_by_name_or_error("str").type == LogicArray(
            dimensions=[
                Dimensions(ElaboratableValue(127)),
                Dimensions(ElaboratableValue(7)),
            ],
            item=Bit(),
        )
        assert sseq_mod.ports.find_by_name_or_error("control").type == BitStruct(
            fields=[StructField(name="full", type=Bit()), StructField(name="forward", type=Bit())]
        )

        # seq_to_sci4_bridges
        assert seq_sci_mod.id.name == "seq_to_sci4_bridge"
        assert len(seq_sci_mod.ports) == 2
        assert (
            seq_sci_mod.ports.find_by_name_or_error("control").type
            == sseq_mod.ports.find_by_name_or_error("control").type
        )
        assert len(seq_sci_mod.interfaces) == 1
        intf = seq_sci_mod.interfaces[0]
        assert intf.mode == InterfaceMode.SUBORDINATE
        assert intf.definition is mod.interfaces[0].definition
        assert not intf.has_sliced_signals

        # char_processor
        assert proc_mod.id.name == "char_processor"
        assert proc_mod.ports.find_by_name_or_error("sci_control").type == BitStruct(
            fields=[
                StructField(name="addr", type=Bits(dimensions=[Dimensions(ElaboratableValue(31))])),
                StructField(name="write", type=Bit()),
                StructField(name="strb", type=Bits(dimensions=[Dimensions(ElaboratableValue(7))])),
                StructField(name="ack", type=Bit()),
            ]
        )
        assert proc_mod.ports.find_by_name_or_error("cows").type == BitStruct(
            name="cow_struct",
            fields=[
                StructField(name="enc", type=Bits(dimensions=[Dimensions(ElaboratableValue(7))])),
                StructField(
                    name="length", type=Bits(dimensions=[Dimensions(ElaboratableValue(31))])
                ),
            ],
        )
        assert proc_mod.ports.find_by_name_or_error("plain_wdata").type == Bits(
            dimensions=[Dimensions(ElaboratableValue(63))]
        )
        assert len(proc_mod.interfaces) == 2
        isci = proc_mod.interfaces.find_by_name_or_error("SCI")
        esci = proc_mod.interfaces.find_by_name_or_error("externally_controlled_SCI")
        assert isci.mode == InterfaceMode.MANAGER
        assert esci.mode == InterfaceMode.SUBORDINATE
        assert isci.has_independent_signals and isci.has_sliced_signals
        assert esci.has_independent_signals and isci.has_sliced_signals
        assert isci.definition is esci.definition is idef
        for sig in ("rdata", "wdata", "sack"):
            assert idef.signals.find_by_name_or_error(sig) in isci.independent_signals
        for sig in ("addr", "write", "strb", "ack"):
            assert idef.signals.find_by_name_or_error(sig) in isci.sliced_signals
        for sig in ("ack", "wdata", "sack"):
            assert idef.signals.find_by_name_or_error(sig) in esci.sliced_signals
        for intf in (isci, esci):
            for sliced in intf.sliced_signals:
                ref = intf.signals[sliced._id]
                assert ref is not None and ref.io in proc_mod.ports

        # TODO: implement design validation when needed
        # Possibly when the SV frontend can parse designs

    @staticmethod
    def ir_inverted(mod: Module):
        assert mod.id == Identifier(name="inv_top")

        ports = [(p.name, p.direction) for p in mod.ports]
        assert all(
            n in ports
            for n in (
                ("clkin", PortDirection.IN),
                ("val", PortDirection.IN),
                ("sum", PortDirection.OUT),
            )
        )

        assert len(mod.interfaces) == 0

        assert mod.design is not None
        components = [c.name for c in mod.design.components]
        assert all(n in components for n in ["adder1", "adder2", "crg"])

        adder1 = mod.design.components.find_by_name_or_error("adder1")
        adder2 = mod.design.components.find_by_name_or_error("adder2")
        crg = mod.design.components.find_by_name_or_error("crg")
        assert adder1.module is inv_adder
        assert adder2.module is inv_adder
        assert crg.module is inv_crg

        assert len(mod.design.connections) == 8

        def _ref_str(io: Union[ReferencedPort, ReferencedInterface, ElaboratableValue]) -> str:
            if isinstance(io, ElaboratableValue):
                return io.value
            inst_name = io.instance.name if io.instance else "<external>"
            return f"{inst_name}.{io.io.name}"

        def _ref_tuple(
            connection: Union[ConstantConnection, InterfaceConnection, PortConnection],
        ) -> tuple[str, ...]:
            return tuple(sorted((_ref_str(connection.target), _ref_str(connection.source))))

        conns = {
            _ref_tuple(connection): isinstance(connection, PortConnection) and connection.invert
            for connection in mod.design.connections
        }

        assert conns == {
            ("<external>.clkin", "crg.clkin"): False,
            ("32", "adder1.a"): False,
            ("<external>.val", "adder1.b"): True,
            ("adder1.enable", "crg.rstout"): True,
            ("adder1.out", "adder2.a"): True,
            ("33", "adder2.b"): False,
            ("adder2.enable", "crg.rstout"): True,
            ("<external>.sum", "adder2.out"): True,
        }

    @staticmethod
    def ir_clocks(mod: Module):
        assert mod.design is not None

        des = mod.design

        clk_port = mod.ports.find_by_name_or_error("clk")
        rst_port = mod.ports.find_by_name_or_error("rst")
        fast_clk_port = mod.ports.find_by_name_or_error("fast_clk")

        assert clk_port.direction is PortDirection.IN
        assert rst_port.direction is PortDirection.IN
        assert fast_clk_port.direction is PortDirection.IN

        assert len(des.components) == 3
        assert len(des.clock_domains) == 2
        assert len(des.reset_domains) == 1
        assert len(des.connections) == 9

        default_clk_dom = des.clock_domains.find_by_name_or_error("default")
        fast_clk_dom = des.clock_domains.find_by_name_or_error("fast")
        default_rst_dom = des.reset_domains.find_by_name_or_error("default")

        assert default_clk_dom.clock == ReferencedPort.external(clk_port)
        assert fast_clk_dom.clock == ReferencedPort.external(fast_clk_port)
        assert default_rst_dom.reset == ReferencedPort.external(rst_port)
        assert default_rst_dom.polarity == ResetPolarity.ACTIVE_HIGH
        assert default_rst_dom.synchronous_to is None

        streamer = des.components.find_by_name_or_error("streamer")
        receiver = des.components.find_by_name_or_error("receiver")
        cdc = des.components.find_by_name_or_error("cdc")

        assert len(streamer.module.clocks) == 1
        assert streamer.module.clocks[0].clock == streamer.module.ports.find_by_name_or_error("clk")
        assert len(streamer.module.resets) == 1
        assert streamer.module.resets[0].reset == streamer.module.ports.find_by_name_or_error("rst")
        assert streamer.module.resets[0].polarity == ResetPolarity.ACTIVE_HIGH
        assert streamer.module.resets[0].synchronous_to is None

        assert len(receiver.module.clocks) == 1
        assert receiver.module.clocks[0].clock == receiver.module.ports.find_by_name_or_error("clk")
        assert len(receiver.module.resets) == 1
        assert receiver.module.resets[0].reset == receiver.module.ports.find_by_name_or_error("rst")
        assert receiver.module.resets[0].polarity == ResetPolarity.ACTIVE_HIGH
        assert receiver.module.resets[0].synchronous_to is None

        assert len(cdc.module.clocks) == 2
        assert cdc.module.clocks[0].clock == cdc.module.ports.find_by_name_or_error("clk_a")
        assert cdc.module.clocks[1].clock == cdc.module.ports.find_by_name_or_error("clk_b")
        assert len(cdc.module.resets) == 1
        assert cdc.module.resets[0].reset == cdc.module.ports.find_by_name_or_error("rst")
        assert cdc.module.resets[0].polarity == ResetPolarity.ACTIVE_HIGH
        assert cdc.module.resets[0].synchronous_to is None

        assert streamer.clocks == {
            streamer.module.clocks[0]._id: fast_clk_dom,
        }
        assert cdc.clocks == {
            cdc.module.clocks[0]._id: fast_clk_dom,
            cdc.module.clocks[1]._id: default_clk_dom,
        }
        assert receiver.clocks == {
            receiver.module.clocks[0]._id: default_clk_dom,
        }

        def _ref_str(io: Union[ReferencedPort, ReferencedInterface, ElaboratableValue]) -> str:
            if isinstance(io, ElaboratableValue):
                return io.value
            inst_name = io.instance.name if io.instance else "<external>"
            return f"{inst_name}.{io.io.name}"

        def _ref_tuple(
            connection: Union[ConstantConnection, InterfaceConnection, PortConnection],
        ) -> tuple[str, ...]:
            return tuple(sorted((_ref_str(connection.target), _ref_str(connection.source))))

        conns = set(_ref_tuple(connection) for connection in mod.design.connections)

        print(conns)

        assert conns == {
            ("cdc.io_a", "streamer.io"),
            ("cdc.io_b", "receiver.io"),
            ("<external>.fast_clk", "streamer.clk"),
            ("<external>.rst", "streamer.rst"),
            ("<external>.clk", "receiver.clk"),
            ("<external>.rst", "receiver.rst"),
            ("<external>.fast_clk", "cdc.clk_a"),
            ("<external>.clk", "cdc.clk_b"),
            ("<external>.rst", "cdc.rst"),
        }

    @pytest.mark.parametrize(
        ["mod", "validator"],
        [
            (simp_top, lambda: TestIrExamples.ir_simple),
            (hier_top, lambda: TestIrExamples.ir_hierarchy),
            (intf_top, lambda: TestIrExamples.ir_interface),
            (intr_top, lambda: TestIrExamples.ir_interconnect),
            (adv_top, lambda: TestIrExamples.ir_advanced),
            (inv_top, lambda: TestIrExamples.ir_inverted),
            (clk_top, lambda: TestIrExamples.ir_clocks),
        ],
    )
    def test_ir_example(self, mod: Module, validator):
        validator()(mod)
