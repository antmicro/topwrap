from topwrap.model.connections import (
    ConstantConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .inv_adder import inv_adder
from .inv_crg import inv_crg

inst_crg = ModuleInstance(name="crg", module=inv_crg)

adder1 = ModuleInstance(name="adder1", module=inv_adder)
adder2 = ModuleInstance(name="adder2", module=inv_adder)

external_ports = [
    Port(name="clkin", direction=PortDirection.IN),
    Port(
        name="val",
        direction=PortDirection.IN,
        type=Bits(
            dimensions=[Dimensions(upper=ElaboratableValue("7"), lower=ElaboratableValue("0"))]
        ),
    ),
    Port(
        name="sum",
        direction=PortDirection.OUT,
        type=Bits(
            dimensions=[Dimensions(upper=ElaboratableValue("8"), lower=ElaboratableValue("0"))]
        ),
    ),
]

module = Module(
    id=Identifier(name="inv_top"),
    ports=external_ports,
    design=Design(
        components=[inst_crg, adder1, adder2],
        connections=[
            PortConnection(
                source=ReferencedPort(instance=inst_crg, io=inv_crg.ports[0]),
                target=ReferencedPort.external(external_ports[0]),
            ),
            ConstantConnection(
                source=ElaboratableValue("32"),
                target=ReferencedPort(instance=adder1, io=inv_adder.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort.external(external_ports[1]),
                target=ReferencedPort(instance=adder1, io=inv_adder.ports[2]),
                invert=True,
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_crg, io=inv_crg.ports[2]),
                target=ReferencedPort(instance=adder1, io=inv_adder.ports[0]),
                invert=True,
            ),
            PortConnection(
                source=ReferencedPort(instance=adder2, io=inv_adder.ports[1]),
                target=ReferencedPort(instance=adder1, io=inv_adder.ports[3]),
                invert=True,
            ),
            ConstantConnection(
                source=ElaboratableValue("33"),
                target=ReferencedPort(instance=adder2, io=inv_adder.ports[2]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_crg, io=inv_crg.ports[2]),
                target=ReferencedPort(instance=adder2, io=inv_adder.ports[0]),
                invert=True,
            ),
            PortConnection(
                source=ReferencedPort(instance=adder2, io=inv_adder.ports[3]),
                target=ReferencedPort.external(external_ports[2]),
                invert=True,
            ),
        ],
    ),
)
