# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import pytest

from examples.ir_examples.interface.ir.receiver import axi_stream
from topwrap.model.connections import (
    Clock,
    InterfaceConnection,
    Port,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.design import (
    ClockDomain,
    Design,
    DesignDomainException,
    ModuleInstance,
    ResetDomain,
)
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

ports1 = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
]
clk1 = Clock(name="default", clock=ports1[0])
rst1 = Reset(
    name="default",
    reset=ports1[1],
    polarity=ResetPolarity.ACTIVE_HIGH,
    synchronous_to=clk1,
)
mod1 = Module(
    id=Identifier(name="mod1"),
    ports=ports1,
    clocks=[clk1],
    resets=[rst1],
)


class TestClockReset:
    def test_lowering(self):
        mod = Module(
            id=Identifier(name="mod2"),
            ports=[
                Port(name="clk", direction=PortDirection.IN),
                Port(name="rst", direction=PortDirection.IN),
            ],
        )

        clk_dom = ClockDomain(name="default", clock=ReferencedPort.external(mod.ports[0]))
        rst_dom = ResetDomain(
            name="default",
            reset=ReferencedPort.external(mod.ports[1]),
            polarity=ResetPolarity.ACTIVE_HIGH,
            synchronous_to=clk_dom,
        )

        mod1inst = ModuleInstance(
            name="mod1",
            module=mod1,
            clocks={clk1._id: clk_dom},
            resets={rst1._id: rst_dom},
        )

        mod.design = des = Design(
            components=[mod1inst],
            clock_domains=[clk_dom],
            reset_domains=[rst_dom],
        )

        des.lower_domains()

        assert len(des.connections) == 2

    def test_reset_polarity(self):
        mod = Module(
            id=Identifier(name="mod2"),
            ports=[
                Port(name="clk", direction=PortDirection.IN),
                Port(name="rst", direction=PortDirection.IN),
            ],
        )

        clk_dom = ClockDomain(name="default", clock=ReferencedPort.external(mod.ports[0]))
        rst_dom = ResetDomain(
            name="default",
            reset=ReferencedPort.external(mod.ports[1]),
            polarity=ResetPolarity.ACTIVE_LOW,
            synchronous_to=clk_dom,
        )

        mod1inst = ModuleInstance(
            name="mod1",
            module=mod1,
            clocks={clk1._id: clk_dom},
            resets={rst1._id: rst_dom},
        )

        mod.design = des = Design(
            components=[mod1inst],
            clock_domains=[clk_dom],
            reset_domains=[rst_dom],
        )

        des.lower_domains()

        assert len(des.connections) == 2

    def test_reset_async_to_sync(self):
        mod = Module(
            id=Identifier(name="mod2"),
            ports=[
                Port(name="clk", direction=PortDirection.IN),
                Port(name="rst", direction=PortDirection.IN),
            ],
        )

        clk_dom = ClockDomain(name="default", clock=ReferencedPort.external(mod.ports[0]))
        rst_dom = ResetDomain(
            name="default",
            reset=ReferencedPort.external(mod.ports[1]),
            polarity=ResetPolarity.ACTIVE_HIGH,
        )

        mod1inst = ModuleInstance(
            name="mod1",
            module=mod1,
            clocks={clk1._id: clk_dom},
            resets={rst1._id: rst_dom},
        )

        mod.design = des = Design(
            components=[mod1inst],
            clock_domains=[clk_dom],
            reset_domains=[rst_dom],
        )

        with pytest.raises(
            DesignDomainException, match="is connected to asynchronous reset domain"
        ):
            des.lower_domains()

    def test_reset_sync_to_sync(self):
        mod = Module(
            id=Identifier(name="mod2"),
            ports=[
                Port(name="clk1", direction=PortDirection.IN),
                Port(name="clk2", direction=PortDirection.IN),
                Port(name="rst", direction=PortDirection.IN),
            ],
        )

        clk1_dom = ClockDomain(name="default", clock=ReferencedPort.external(mod.ports[0]))
        clk2_dom = ClockDomain(name="clk2", clock=ReferencedPort.external(mod.ports[1]))
        rst_dom = ResetDomain(
            name="default",
            reset=ReferencedPort.external(mod.ports[2]),
            polarity=ResetPolarity.ACTIVE_HIGH,
            synchronous_to=clk2_dom,
        )

        mod1inst = ModuleInstance(
            name="mod1",
            module=mod1,
            clocks={clk1._id: clk1_dom},
            resets={rst1._id: rst_dom},
        )

        mod.design = des = Design(
            components=[mod1inst],
            clock_domains=[clk1_dom, clk2_dom],
            reset_domains=[rst_dom],
        )

        with pytest.raises(DesignDomainException, match="which is synchronous to clock domain"):
            des.lower_domains()

    def test_intf_cdc(self):
        top = Module(
            id=Identifier(name="top"),
            ports=[
                Port(name="clk1", direction=PortDirection.IN),
                Port(name="clk2", direction=PortDirection.IN),
            ],
        )

        src = Module(
            id=Identifier(name="src"),
            ports=[
                (src_clk_port := Port(name="clk", direction=PortDirection.IN)),
            ],
            clocks=[
                (
                    src_clk := Clock(
                        name="default",
                        clock=src_clk_port,
                    )
                )
            ],
            interfaces=[
                Interface(
                    name="src",
                    mode=InterfaceMode.MANAGER,
                    definition=axi_stream,
                    signals={},
                    clock=src_clk,
                ),
            ],
        )

        dst = Module(
            id=Identifier(name="dst"),
            ports=[
                (dst_clk_port := Port(name="clk", direction=PortDirection.IN)),
            ],
            clocks=[
                (
                    dst_clk := Clock(
                        name="default",
                        clock=dst_clk_port,
                    )
                )
            ],
            interfaces=[
                Interface(
                    name="dst",
                    mode=InterfaceMode.SUBORDINATE,
                    definition=axi_stream,
                    signals={},
                    clock=dst_clk,
                ),
            ],
        )

        clk1_dom = ClockDomain(name="slow", clock=ReferencedPort.external(top.ports[0]))
        clk2_dom = ClockDomain(name="fast", clock=ReferencedPort.external(top.ports[1]))

        src_inst = ModuleInstance(
            name="src",
            module=src,
            clocks={src_clk._id: clk1_dom},
        )

        dst_inst = ModuleInstance(
            name="dst",
            module=dst,
            clocks={dst_clk._id: clk2_dom},
        )

        top.design = des = Design(
            components=[src_inst, dst_inst],
            connections=[
                InterfaceConnection(
                    source=ReferencedInterface(io=src.interfaces[0], instance=src_inst),
                    target=ReferencedInterface(io=dst.interfaces[0], instance=dst_inst),
                ),
            ],
            clock_domains=[clk1_dom, clk2_dom],
        )

        with pytest.raises(DesignDomainException, match="crosses clock domains"):
            des.lower_domains()
