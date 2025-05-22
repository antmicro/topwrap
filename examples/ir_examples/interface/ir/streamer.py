from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions, LogicBitSelect, LogicSelect
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
                axi_stream.signals[2]._id: ReferencedPort.external(ports[2]),
                axi_stream.signals[0]._id: ReferencedPort.external(
                    ports[3],
                    LogicSelect(
                        logic=ports[3].type,
                        ops=[LogicBitSelect(Dimensions(upper=ElaboratableValue("0")))],
                    ),
                ),
                axi_stream.signals[3]._id: ReferencedPort.external(
                    ports[3],
                    LogicSelect(
                        logic=ports[3].type,
                        ops=[
                            LogicBitSelect(
                                Dimensions(
                                    upper=ElaboratableValue("4"), lower=ElaboratableValue("1")
                                )
                            )
                        ],
                    ),
                ),
            },
        )
    ],
)
