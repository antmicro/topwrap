from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

from .wishbone import wishbone

exts = [
    Port(name="sys_clk", direction=PortDirection.IN),
    Port(name="sys_rst", direction=PortDirection.IN),
    Port(name="mem_bus_cyc", direction=PortDirection.IN),
    Port(name="mem_bus_stb", direction=PortDirection.IN),
    Port(
        name="mem_bus_adr",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(29))]),
    ),
    Port(
        name="mem_bus_dat_w",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(31))]),
    ),
    Port(name="mem_bus_we", direction=PortDirection.IN),
    Port(
        name="mem_bus_dat_r",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(31))]),
    ),
    Port(name="mem_bus_ack", direction=PortDirection.OUT),
    Port(
        name="mem_bus_sel",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(3))]),
    ),
    Port(
        name="mem_bus_cti",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(2))]),
    ),
    Port(
        name="mem_bus_bte",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(1))]),
    ),
]

mem = Module(
    id=Identifier(name="mem"),
    ports=exts,
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
                wishbone.signals[7]._id: ReferencedPort.external(exts[11]),
                wishbone.signals[8]._id: ReferencedPort.external(exts[10]),
                wishbone.signals[9]._id: ReferencedPort.external(exts[9]),
            },
        )
    ],
    parameters=[
        Parameter(name="depth", default_value=ElaboratableValue("256")),
        Parameter(name="memfile", default_value=ElaboratableValue('""')),
    ],
)
