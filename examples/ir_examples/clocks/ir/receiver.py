from topwrap.model.connections import (
    Clock,
    Port,
    PortDirection,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.hdl_types import Bits, Dimensions, LogicBitSelect, LogicSelect
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .axistream import axi_stream

ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
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

clocks = [
    Clock(
        name="clk",
        clock=ports[0],
    ),
]

resets = [
    Reset(
        name="rst",
        reset=ports[1],
        polarity=ResetPolarity.ACTIVE_HIGH,
    )
]

axis_clk_receiver = Module(
    id=Identifier(name="axis_clk_receiver"),
    ports=ports,
    interfaces=[
        Interface(
            name="io",
            mode=InterfaceMode.SUBORDINATE,
            definition=axi_stream,
            clock=clocks[0],
            reset=resets[0],
            signals={
                axi_stream.signals[2]._id: ReferencedPort.external(ports[2]),
                axi_stream.signals[0]._id: ReferencedPort.external(
                    ports[3],
                    LogicSelect(
                        logic=ports[3].type,
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
                    ports[3],
                    LogicSelect(
                        logic=ports[3].type,
                        ops=[LogicBitSelect(Dimensions(upper=ElaboratableValue("3")))],
                    ),
                ),
            },
        )
    ],
    clocks=clocks,
    resets=resets,
)
