from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

two_mux = Module(
    id=Identifier(name="2mux_compressor"),
    parameters=[
        Parameter(name="WIDTH", default_value=ElaboratableValue("64")),
        Parameter(name="OUT_WIDTH", default_value=ElaboratableValue("1")),
    ],
    ports=[
        Port(name="gen_sel", direction=PortDirection.IN),
        Port(
            name="gen1",
            direction=PortDirection.IN,
            type=Bits(
                dimensions=[
                    Dimensions(upper=ElaboratableValue("WIDTH-1"), lower=ElaboratableValue("0"))
                ]
            ),
        ),
        Port(
            name="gen2",
            direction=PortDirection.IN,
            type=Bits(
                dimensions=[
                    Dimensions(upper=ElaboratableValue("WIDTH-1"), lower=ElaboratableValue("0"))
                ]
            ),
        ),
        Port(
            name="out",
            direction=PortDirection.OUT,
            type=Bits(
                dimensions=[
                    Dimensions(upper=ElaboratableValue("WIDTH-1"), lower=ElaboratableValue("0"))
                ]
            ),
        ),
    ],
)
