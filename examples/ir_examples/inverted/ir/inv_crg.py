from topwrap.model.connections import Port, PortDirection
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

inv_crg = Module(
    id=Identifier(name="inv_crg"),
    ports=[
        Port(name="clkin", direction=PortDirection.IN),
        Port(name="clkout", direction=PortDirection.OUT),
        Port(name="rstout", direction=PortDirection.OUT),
    ],
)
