from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

inv_adder = Module(
    id=Identifier(name="inv_adder"),
    ports=[
        Port(name="enable", direction=PortDirection.IN),
        Port(
            name="a",
            direction=PortDirection.IN,
            type=Bits(
                dimensions=[Dimensions(upper=ElaboratableValue("7"), lower=ElaboratableValue("0"))]
            ),
        ),
        Port(
            name="b",
            direction=PortDirection.IN,
            type=Bits(
                dimensions=[Dimensions(upper=ElaboratableValue("7"), lower=ElaboratableValue("0"))]
            ),
        ),
        Port(
            name="out",
            direction=PortDirection.OUT,
            type=Bits(
                dimensions=[Dimensions(upper=ElaboratableValue("8"), lower=ElaboratableValue("0"))]
            ),
        ),
    ],
)
