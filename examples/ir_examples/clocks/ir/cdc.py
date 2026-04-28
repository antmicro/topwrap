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
    Port(name="clk_a", direction=PortDirection.IN),
    Port(name="clk_b", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(
        name="a_dat_i",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="a_ctrl_i",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("4"))]),
    ),
    Port(
        name="b_dat_o",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="b_ctrl_o",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("4"))]),
    ),
]

clocks = [
    Clock(
        name="clk_a",
        clock=ports[0],
    ),
    Clock(
        name="clk_b",
        clock=ports[1],
    ),
]

resets = [
    Reset(
        name="rst",
        reset=ports[2],
        polarity=ResetPolarity.ACTIVE_HIGH,
    )
]

axis_cdc = Module(
    id=Identifier(name="axis_cdc"),
    ports=ports,
    interfaces=[
        Interface(
            name="io_a",
            mode=InterfaceMode.SUBORDINATE,
            definition=axi_stream,
            clock=clocks[0],
            reset=resets[0],
            signals={
                axi_stream.signals[2]._id: ReferencedPort.external(ports[3]),
                axi_stream.signals[0]._id: ReferencedPort.external(
                    ports[4],
                    LogicSelect(
                        logic=ports[4].type,
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
                    ports[4],
                    LogicSelect(
                        logic=ports[4].type,
                        ops=[LogicBitSelect(Dimensions(upper=ElaboratableValue("3")))],
                    ),
                ),
            },
        ),
        Interface(
            name="io_b",
            mode=InterfaceMode.MANAGER,
            definition=axi_stream,
            clock=clocks[1],
            reset=resets[0],
            signals={
                axi_stream.signals[2]._id: ReferencedPort.external(ports[5]),
                axi_stream.signals[0]._id: ReferencedPort.external(
                    ports[6],
                    LogicSelect(
                        logic=ports[6].type,
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
                    ports[6],
                    LogicSelect(
                        logic=ports[6].type,
                        ops=[LogicBitSelect(Dimensions(upper=ElaboratableValue("3")))],
                    ),
                ),
            },
        ),
    ],
    clocks=clocks,
    resets=resets,
)
