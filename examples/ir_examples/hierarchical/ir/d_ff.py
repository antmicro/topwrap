from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

d_ff = Module(
    id=Identifier(name="D-flipflop"),
    parameters=[Parameter(name="WIDTH", default_value=ElaboratableValue("4"))],
    ports=[
        Port(name="clk", direction=PortDirection.IN),
        Port(name="rst", direction=PortDirection.IN),
        Port(
            name="D",
            direction=PortDirection.IN,
            type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("WIDTH-1"))]),
        ),
        Port(
            name="Q",
            direction=PortDirection.OUT,
            type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("WIDTH-1"))]),
        ),
    ],
)
