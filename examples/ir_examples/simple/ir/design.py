from topwrap.model.connections import (
    Port,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .lfsr_gen import lfsr_gen
from .two_mux import two_mux

inst_two_mux = ModuleInstance(
    name="2mux", module=two_mux, parameters={two_mux.parameters[0]._id: ElaboratableValue("128")}
)

gen1 = ModuleInstance(
    name="gen1",
    module=lfsr_gen,
    parameters={
        lfsr_gen.parameters[0]._id: ElaboratableValue("128"),
        lfsr_gen.parameters[1]._id: ElaboratableValue("1337"),
    },
)

gen2 = ModuleInstance(
    name="gen2",
    module=lfsr_gen,
    parameters={
        lfsr_gen.parameters[0]._id: ElaboratableValue("128"),
    },
)

external_ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="sel_gen", direction=PortDirection.IN),
    Port(name="rnd_bit", direction=PortDirection.OUT),
]

module = Module(
    id=Identifier(name="top"),
    ports=external_ports,
    design=Design(
        components=[inst_two_mux, gen1, gen2],
        connections=[
            PortConnection(
                source=ReferencedPort(instance=inst_two_mux, io=two_mux.ports[0]),
                target=ReferencedPort.external(external_ports[2]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_two_mux, io=two_mux.ports[1]),
                target=ReferencedPort(instance=gen1, io=lfsr_gen.ports[2]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_two_mux, io=two_mux.ports[2]),
                target=ReferencedPort(instance=gen2, io=lfsr_gen.ports[2]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_two_mux, io=two_mux.ports[3]),
                target=ReferencedPort.external(external_ports[3]),
            ),
            PortConnection(
                source=ReferencedPort(instance=gen1, io=lfsr_gen.ports[0]),
                target=ReferencedPort.external(external_ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=gen1, io=lfsr_gen.ports[1]),
                target=ReferencedPort.external(external_ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=gen2, io=lfsr_gen.ports[0]),
                target=ReferencedPort.external(external_ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=gen2, io=lfsr_gen.ports[1]),
                target=ReferencedPort.external(external_ports[1]),
            ),
        ],
    ),
)
