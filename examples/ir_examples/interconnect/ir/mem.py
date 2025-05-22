from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

from .wishbone import wishbone

exts = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="i_cyc", direction=PortDirection.IN),
    Port(name="i_stb", direction=PortDirection.IN),
    Port(
        name="i_adr",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="i_dat",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("WIDTH-1"))]),
    ),
    Port(name="i_we", direction=PortDirection.IN),
    Port(
        name="o_dat",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("WIDTH-1"))]),
    ),
    Port(name="o_ack", direction=PortDirection.OUT),
    Port(name="o_stall", direction=PortDirection.OUT),
    Port(name="o_err", direction=PortDirection.OUT),
]

mem = Module(
    id=Identifier(name="memory_block"),
    ports=exts,
    parameters=[
        Parameter(name="WIDTH", default_value=ElaboratableValue("32")),
        Parameter(name="DEPTH", default_value=ElaboratableValue("0")),
    ],
    interfaces=[
        Interface(
            name="bus",
            mode=InterfaceMode.SUBORDINATE,
            definition=wishbone,
            signals={
                wishbone.signals[0]._id: ReferencedPort.external(exts[2]),
                wishbone.signals[1]._id: ReferencedPort.external(exts[3]),
                wishbone.signals[2]._id: ReferencedPort.external(exts[8]),
                wishbone.signals[3]._id: ReferencedPort.external(exts[5]),
                wishbone.signals[4]._id: ReferencedPort.external(exts[7]),
                wishbone.signals[5]._id: ReferencedPort.external(exts[4]),
                wishbone.signals[6]._id: ReferencedPort.external(exts[6]),
                wishbone.signals[7]._id: ReferencedPort.external(exts[9]),
                wishbone.signals[8]._id: ReferencedPort.external(exts[10]),
            },
        )
    ],
)
