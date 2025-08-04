from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .wishbone import wishbone

exts = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="reset", direction=PortDirection.IN),
    Port(name="dBusWishbone_CYC", direction=PortDirection.OUT),
    Port(name="dBusWishbone_STB", direction=PortDirection.OUT),
    Port(name="dBusWishbone_ACK", direction=PortDirection.IN),
    Port(
        name="dBusWishbone_DAT_MOSI",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(
        name="dBusWishbone_DAT_MISO",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(
        name="dBusWishbone_ADR",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(29))]),
    ),
    Port(name="dBusWishbone_WE", direction=PortDirection.OUT),
    Port(
        name="dBusWishbone_BTE",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(1))]),
    ),
    Port(
        name="dBusWishbone_CTI",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(2))]),
    ),
    Port(
        name="dBusWishbone_SEL",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(3))]),
    ),
    Port(name="iBusWishbone_CYC", direction=PortDirection.OUT),
    Port(name="iBusWishbone_STB", direction=PortDirection.OUT),
    Port(name="iBusWishbone_ACK", direction=PortDirection.IN),
    Port(
        name="iBusWishbone_DAT_MOSI",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(
        name="iBusWishbone_DAT_MISO",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(
        name="iBusWishbone_ADR",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(29))]),
    ),
    Port(name="iBusWishbone_WE", direction=PortDirection.OUT),
    Port(
        name="iBusWishbone_BTE",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(1))]),
    ),
    Port(
        name="iBusWishbone_CTI",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(2))]),
    ),
    Port(
        name="iBusWishbone_SEL",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(3))]),
    ),
    Port(
        name="externalResetVector",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(
        name="externalInterruptArray",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(name="softwareInterrupt", direction=PortDirection.IN),
    Port(name="timerInterrupt", direction=PortDirection.IN),
]

vex_riscv = Module(
    id=Identifier(name="VexRiscv"),
    ports=exts,
    interfaces=[
        Interface(
            name="dBusWishbone",
            mode=InterfaceMode.MANAGER,
            definition=wishbone,
            signals={
                wishbone.signals[0]._id: ReferencedPort.external(exts[2]),
                wishbone.signals[1]._id: ReferencedPort.external(exts[3]),
                wishbone.signals[2]._id: ReferencedPort.external(exts[4]),
                wishbone.signals[3]._id: ReferencedPort.external(exts[5]),
                wishbone.signals[4]._id: ReferencedPort.external(exts[6]),
                wishbone.signals[5]._id: ReferencedPort.external(exts[7]),
                wishbone.signals[6]._id: ReferencedPort.external(exts[8]),
                wishbone.signals[7]._id: ReferencedPort.external(exts[9]),
                wishbone.signals[8]._id: ReferencedPort.external(exts[10]),
                wishbone.signals[9]._id: ReferencedPort.external(exts[11]),
            },
        ),
        Interface(
            name="iBusWishbone",
            mode=InterfaceMode.MANAGER,
            definition=wishbone,
            signals={
                wishbone.signals[0]._id: ReferencedPort.external(exts[12]),
                wishbone.signals[1]._id: ReferencedPort.external(exts[13]),
                wishbone.signals[2]._id: ReferencedPort.external(exts[14]),
                wishbone.signals[3]._id: ReferencedPort.external(exts[15]),
                wishbone.signals[4]._id: ReferencedPort.external(exts[16]),
                wishbone.signals[5]._id: ReferencedPort.external(exts[17]),
                wishbone.signals[6]._id: ReferencedPort.external(exts[18]),
                wishbone.signals[7]._id: ReferencedPort.external(exts[19]),
                wishbone.signals[8]._id: ReferencedPort.external(exts[20]),
                wishbone.signals[9]._id: ReferencedPort.external(exts[21]),
            },
        ),
    ],
)
