from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .wishbone import wishbone

exts = [
    Port(name="sys_clk", direction=PortDirection.IN),
    Port(name="sys_rst", direction=PortDirection.IN),
    Port(name="csr_wishbone_cyc", direction=PortDirection.IN),
    Port(name="csr_wishbone_stb", direction=PortDirection.IN),
    Port(
        name="csr_wishbone_adr",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(29))]),
    ),
    Port(
        name="csr_wishbone_mosi",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(31))]),
    ),
    Port(name="csr_wishbone_we", direction=PortDirection.IN),
    Port(
        name="csr_wishbone_miso",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(31))]),
    ),
    Port(name="csr_wishbone_ack", direction=PortDirection.OUT),
    Port(
        name="csr_wishbone_sel",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(3))]),
    ),
    Port(
        name="csr_wishbone_cti",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(2))]),
    ),
    Port(
        name="csr_wishbone_bte",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(1))]),
    ),
    Port(name="serial1_tx", direction=PortDirection.OUT),
    Port(name="serial1_rx", direction=PortDirection.IN),
]

uart = Module(
    id=Identifier(name="wb_uart"),
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
)
