from topwrap.model.connections import Port, PortDirection
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

debouncer = Module(
    id=Identifier(name="debouncer"),
    parameters=[Parameter(name="GRACE", default_value=ElaboratableValue("1000"))],
    ports=[
        Port(name="clk", direction=PortDirection.IN),
        Port(name="in", direction=PortDirection.IN),
        Port(name="filtered_out", direction=PortDirection.OUT),
    ],
)
