from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

_width = Parameter(name="WIDTH", default_value=ElaboratableValue("4"))
_dims = [Dimensions(upper=ElaboratableValue("WIDTH-1"))]

adder = Module(
    id=Identifier(name="adder"),
    parameters=[_width],
    ports=[
        Port(name="a", direction=PortDirection.IN, type=Bits(dimensions=_dims)),
        Port(name="b", direction=PortDirection.IN, type=Bits(dimensions=_dims)),
        Port(name="sum", direction=PortDirection.OUT, type=Bits(dimensions=_dims)),
    ],
)
