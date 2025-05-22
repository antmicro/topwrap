from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .wishbone import wishbone

exts = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="o_wb_cyc", direction=PortDirection.OUT),
    Port(name="o_wb_stb", direction=PortDirection.OUT),
    Port(
        name="o_wb_adr",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="o_wb_dat",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("7"))]),
    ),
    Port(name="o_wb_we", direction=PortDirection.OUT),
    Port(
        name="i_wb_dat",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("7"))]),
    ),
    Port(name="i_wb_ack", direction=PortDirection.IN),
    Port(name="i_wb_stall", direction=PortDirection.IN),
    Port(name="i_wb_err", direction=PortDirection.IN),
]

cpu = Module(
    id=Identifier(name="cpu"),
    ports=exts,
    interfaces=[
        Interface(
            name="bus_manager",
            mode=InterfaceMode.MANAGER,
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
