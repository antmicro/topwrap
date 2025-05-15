from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

lfsr_gen = Module(
    id=Identifier(name="lfsr_gen"),
    parameters=[
        Parameter(name="WIDTH", default_value=ElaboratableValue("64")),
        Parameter(name="SEED", default_value=ElaboratableValue("1")),
    ],
    ports=[
        Port(name="clk", direction=PortDirection.IN),
        Port(name="rst", direction=PortDirection.IN),
        Port(
            name="gen_out",
            direction=PortDirection.OUT,
            type=Bits(
                dimensions=[
                    Dimensions(upper=ElaboratableValue("WIDTH-1"), lower=ElaboratableValue("0"))
                ]
            ),
        ),
    ],
)
