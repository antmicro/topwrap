from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions, LogicSlice
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
                wishbone.signals[0]._id: LogicSlice(logic=exts[2].type),
                wishbone.signals[1]._id: LogicSlice(logic=exts[3].type),
                wishbone.signals[2]._id: LogicSlice(logic=exts[8].type),
                wishbone.signals[3]._id: LogicSlice(logic=exts[5].type),
                wishbone.signals[4]._id: LogicSlice(logic=exts[7].type),
                wishbone.signals[5]._id: LogicSlice(logic=exts[4].type),
                wishbone.signals[6]._id: LogicSlice(logic=exts[6].type),
                wishbone.signals[7]._id: LogicSlice(logic=exts[9].type),
                wishbone.signals[8]._id: LogicSlice(logic=exts[10].type),
            },
        )
    ],
)
