# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from examples.ir_examples.modules import (
    hier_top,
    intf_top,
    intr_top,
    lfsr_gen,
    simp_top,
    two_mux,
)
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    PortDirection,
)
from topwrap.model.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRFeature,
    WishboneRRParams,
)
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import Identifier
from topwrap.model.module import Module


class TestIrExamples:
    """
    Tests based on IR examples for frontends that verify whether
    a top-level Module parsed by a them matches up with the original
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
        assert intf.source.io.signals[tvalid._id].logic.outer.name == "ctrl_o"

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
        assert intr.clock.io.logic.outer.name == "clk"
        assert intr.reset.io.logic.outer.name == "rst"
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
        assert ext.is_external
        dsp, mem = intr.subordinates.items()
        assert dsp[0].resolve().instance.name == "dsp"

        assert mem[1].address.value == "65536"
        assert mem[1].size.value == "255"

    @pytest.mark.parametrize(
        ["mod", "validator"],
        [
            (simp_top, lambda: TestIrExamples.ir_simple),
            (hier_top, lambda: TestIrExamples.ir_hierarchy),
            (intf_top, lambda: TestIrExamples.ir_interface),
            (intr_top, lambda: TestIrExamples.ir_interconnect),
        ],
    )
    def test_ir_example(self, mod: Module, validator):
        validator()(mod)
