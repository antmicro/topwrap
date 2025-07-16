# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.interconnects.axi import (
    AXIInterconnect,
    AXIManagerParams,
    AXIParams,
    AXISubordinateParams,
)
from topwrap.model.connections import (
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .simple_manager import simple_manager
from .uart import uart

inst_uart0 = ModuleInstance(
    name="uart0",
    module=uart,
)
inst_uart1 = ModuleInstance(
    name="uart1",
    module=uart,
)
inst_simple_manager = ModuleInstance(
    name="inst_simple_manager",
    module=simple_manager,
)

extp = [
    Port(name="clk100", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="serial0_rx", direction=PortDirection.IN),
    Port(name="serial0_tx", direction=PortDirection.OUT),
    Port(name="serial1_rx", direction=PortDirection.IN),
    Port(name="serial1_tx", direction=PortDirection.OUT),
]

design = Design(
    components=[inst_uart0, inst_uart1, inst_simple_manager],
    connections=[
        PortConnection(
            source=ReferencedPort(instance=inst_uart0, io=uart.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart0, io=uart.ports[1]),
            target=ReferencedPort.external(extp[1]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart0, io=uart.ports[2]),
            target=ReferencedPort.external(extp[2]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart0, io=uart.ports[3]),
            target=ReferencedPort.external(extp[3]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart1, io=uart.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart1, io=uart.ports[1]),
            target=ReferencedPort.external(extp[1]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart1, io=uart.ports[2]),
            target=ReferencedPort.external(extp[4]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart1, io=uart.ports[3]),
            target=ReferencedPort.external(extp[5]),
        ),
    ],
    interconnects=[
        AXIInterconnect(
            name="AXI_bus",
            clock=ReferencedPort.external(extp[0]),
            reset=ReferencedPort.external(extp[1]),
            params=AXIParams(
                atop=False,
            ),
            managers={
                ReferencedInterface(
                    instance=inst_simple_manager, io=simple_manager.interfaces[0]
                )._id: AXIManagerParams(id_width=ElaboratableValue(3))
            },
            subordinates={
                ReferencedInterface(
                    instance=inst_uart0, io=uart.interfaces[0]
                )._id: AXISubordinateParams(
                    address=ElaboratableValue(0xF0000000), size=ElaboratableValue(0x1000)
                ),
                ReferencedInterface(
                    instance=inst_uart1, io=uart.interfaces[0]
                )._id: AXISubordinateParams(
                    address=ElaboratableValue(0xF0001000), size=ElaboratableValue(0x1000)
                ),
            },
        )
    ],
)

top = Module(
    id=Identifier(name="axi_interconnect_top"),
    ports=extp,
    design=design,
)
