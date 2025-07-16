# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .axi import axi_signals, interconnect_axi

id = Identifier(name="simple_manager")

exts = [
    Port(name="sys_clk", direction=PortDirection.IN),
    Port(name="sys_rst", direction=PortDirection.IN),
]

signals = {}

for i, (ch, name, direction, _width) in enumerate(axi_signals):
    port = Port(
        name=f"{'i' if direction else 'o'}_{id.name}_{ch}{name}",
        direction=PortDirection.IN if direction else PortDirection.OUT,
    )
    exts.append(port)
    signals[interconnect_axi.signals[i]._id] = ReferencedPort.external(port)

simple_manager = Module(
    id=id,
    ports=exts,
    interfaces=[
        Interface(
            name="bus",
            mode=InterfaceMode.MANAGER,
            definition=interconnect_axi,
            signals=signals,
        )
    ],
)
