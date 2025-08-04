from topwrap.model.connections import Port, PortDirection
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

exts = [
    Port(name="clk100", direction=PortDirection.IN),
    Port(name="sys_clk", direction=PortDirection.OUT),
    Port(name="sys_rst", direction=PortDirection.OUT),
]

crg = Module(
    id=Identifier(name="crg"),
    ports=exts,
    parameters=[
        Parameter(name="depth", default_value=ElaboratableValue("256")),
    ],
)
