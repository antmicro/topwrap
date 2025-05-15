from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions, LogicSlice
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .axistream import axi_stream

ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(
        name="dat_o",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="ctrl_o",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("4"))]),
    ),
]

axis_streamer = Module(
    id=Identifier(name="axis_streamer"),
    ports=ports,
    interfaces=[
        Interface(
            name="io",
            mode=InterfaceMode.MANAGER,
            definition=axi_stream,
            signals={
                axi_stream.signals[2]._id: LogicSlice(logic=ports[2].type),
                axi_stream.signals[0]._id: LogicSlice(
                    logic=ports[3].type, upper=ElaboratableValue("0")
                ),
                axi_stream.signals[3]._id: LogicSlice(
                    logic=ports[3].type, upper=ElaboratableValue("4"), lower=ElaboratableValue("1")
                ),
            },
        )
    ],
)
