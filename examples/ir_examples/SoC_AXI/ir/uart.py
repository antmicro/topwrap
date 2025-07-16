# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .axi import axi_signals, interconnect_axi

id = Identifier(name="wb_uart")

exts = [
    Port(name="sys_clk", direction=PortDirection.IN),
    Port(name="sys_rst", direction=PortDirection.IN),
    Port(name="serial1_rx", direction=PortDirection.IN),
    Port(name="serial1_tx", direction=PortDirection.OUT),
]

signals = {}

for i, (ch, name, direction, _) in enumerate(axi_signals):
    port = Port(
        name=f"{'o' if direction else 'i'}_{id.name}_{ch}{name}",
        direction=PortDirection.OUT if direction else PortDirection.IN,
    )
    exts.append(port)
    signals[interconnect_axi.signals[i]._id] = ReferencedPort.external(port)

uart = Module(
    id=id,
    ports=exts,
    interfaces=[
        Interface(
            name="bus",
            mode=InterfaceMode.SUBORDINATE,
            definition=interconnect_axi,
            signals=signals,
        )
    ],
)
