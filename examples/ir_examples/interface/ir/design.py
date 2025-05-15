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
from topwrap.model.hdl_types import LogicSlice
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .receiver import axis_receiver
from .streamer import axis_streamer

streamer = ModuleInstance(name="streamer", module=axis_streamer)
receiver = ModuleInstance(name="receiver", module=axis_receiver)

external_ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="ext", direction=PortDirection.INOUT),
]

module = Module(
    id=Identifier(name="top"),
    ports=external_ports,
    design=Design(
        components=[streamer, receiver],
        connections=[
            PortConnection(
                source=ReferencedPort(
                    instance=streamer, io=LogicSlice(logic=axis_streamer.ports[0].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=external_ports[0].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=streamer, io=LogicSlice(logic=axis_streamer.ports[1].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=external_ports[1].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=receiver, io=LogicSlice(logic=axis_receiver.ports[0].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=external_ports[0].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=receiver, io=LogicSlice(logic=axis_receiver.ports[1].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=external_ports[1].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=receiver, io=LogicSlice(logic=axis_receiver.ports[3].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=external_ports[2].type)),
            ),
            ConstantConnection(
                source=ElaboratableValue("2888"),
                target=ReferencedPort(
                    instance=receiver, io=LogicSlice(logic=axis_receiver.ports[2].type)
                ),
            ),
            InterfaceConnection(
                source=ReferencedInterface(instance=streamer, io=axis_streamer.interfaces[0]),
                target=ReferencedInterface(instance=receiver, io=axis_receiver.interfaces[0]),
            ),
        ],
    ),
)
