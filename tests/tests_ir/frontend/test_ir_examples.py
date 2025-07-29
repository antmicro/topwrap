# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from examples.ir_examples.advanced.ir.types import sci_intf
from examples.ir_examples.modules import (
    adv_top,
    hier_top,
    intf_top,
    intr_top,
    lfsr_gen,
    proc_mod,
    seq_sci_mod,
    simp_top,
    sseq_mod,
    two_mux,
)
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    PortDirection,
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
from topwrap.model.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRFeature,
    WishboneRRParams,
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

        gen1 = next(c for c in mod.design.components if c.name == "gen1")
        mux2 = next(c for c in mod.design.components if c.name == "2mux")
        param = next(v for p, v in gen1.parameters.items() if p.resolve().name == "SEED")
        assert param.value == "1337"
        assert gen1.module is lfsr_gen
        assert mux2.module is two_mux

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

        assert intf.source.instance.name == "streamer"
        assert intf.target.instance.name == "receiver"
        assert (defi := intf.target.io.definition) is intf.source.io.definition
        assert defi.id.name == "AXI 4 Stream"
        assert intf.source.io.mode == InterfaceMode.MANAGER
        assert intf.target.io.mode == InterfaceMode.SUBORDINATE
        tvalid = next(s for s in defi.signals if s.name == "TVALID")
        assert intf.source.io.signals[tvalid._id].io.name == "ctrl_o"

        assert len(intf.target.instance.module.ports) == 6
        ctrl_i = intf.target.instance.module.ports.find_by_name("ctrl_i").type
        assert isinstance(ctrl_i, Bits)
        assert ctrl_i.dimensions[0].upper == ElaboratableValue(4)
        assert ctrl_i.dimensions[0].lower == ElaboratableValue(0)
        signal = intf.target.io.signals[defi.signals.find_by_name("TVALID")._id]
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

    @pytest.mark.parametrize(
        ["mod", "validator"],
        [
            (simp_top, lambda: TestIrExamples.ir_simple),
            (hier_top, lambda: TestIrExamples.ir_hierarchy),
            (intf_top, lambda: TestIrExamples.ir_interface),
            (intr_top, lambda: TestIrExamples.ir_interconnect),
            (adv_top, lambda: TestIrExamples.ir_advanced),
        ],
    )
    def test_ir_example(self, mod: Module, validator):
        validator()(mod)
