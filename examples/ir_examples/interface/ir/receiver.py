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
        name="noise",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("15"))]),
    ),
    Port(
        name="ext",
        direction=PortDirection.INOUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="dat_i",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="ctrl_i",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("4"))]),
    ),
]

axis_receiver = Module(
    id=Identifier(name="axis_receiver"),
    ports=ports,
    interfaces=[
        Interface(
            name="io",
            mode=InterfaceMode.SUBORDINATE,
            definition=axi_stream,
            signals={
                axi_stream.signals[2]._id: ReferencedPort.external(ports[4]),
                axi_stream.signals[0]._id: ReferencedPort.external(
                    ports[5],
                    LogicSelect(
                        logic=ports[5].type,
                        ops=[
                            LogicBitSelect(
                                Dimensions(
                                    upper=ElaboratableValue("4"), lower=ElaboratableValue("4")
                                )
                            )
                        ],
                    ),
                ),
                axi_stream.signals[3]._id: ReferencedPort.external(
                    ports[5],
                    LogicSelect(
                        logic=ports[5].type,
                        ops=[LogicBitSelect(Dimensions(upper=ElaboratableValue("3")))],
                    ),
                ),
            },
        )
    ],
)
