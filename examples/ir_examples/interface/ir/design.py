from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .receiver import axis_receiver
from .streamer import axis_streamer

streamer = ModuleInstance(name="streamer", module=axis_streamer)
receiver = ModuleInstance(name="receiver", module=axis_receiver)

external_ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(
        name="ext",
        direction=PortDirection.INOUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue("31"))]),
    ),
]

module = Module(
    id=Identifier(name="top"),
    ports=external_ports,
    design=Design(
        components=[streamer, receiver],
        connections=[
            PortConnection(
                source=ReferencedPort(instance=streamer, io=axis_streamer.ports[0]),
                target=ReferencedPort.external(external_ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=streamer, io=axis_streamer.ports[1]),
                target=ReferencedPort.external(external_ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=receiver, io=axis_receiver.ports[0]),
                target=ReferencedPort.external(external_ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=receiver, io=axis_receiver.ports[1]),
                target=ReferencedPort.external(external_ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=receiver, io=axis_receiver.ports[3]),
                target=ReferencedPort.external(external_ports[2]),
            ),
            ConstantConnection(
                source=ElaboratableValue("2888"),
                target=ReferencedPort(instance=receiver, io=axis_receiver.ports[2]),
            ),
            InterfaceConnection(
                source=ReferencedInterface(instance=streamer, io=axis_streamer.interfaces[0]),
                target=ReferencedInterface(instance=receiver, io=axis_receiver.interfaces[0]),
            ),
        ],
    ),
)
