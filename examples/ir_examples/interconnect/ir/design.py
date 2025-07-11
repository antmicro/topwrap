from topwrap.model.connections import (
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRFeature,
    WishboneRRManagerParams,
    WishboneRRParams,
    WishboneRRSubordinateParams,
)
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .cpu import cpu
from .dsp import dsp
from .mem import mem
from .wishbone import wishbone

inst_cpu = ModuleInstance(name="cpu", module=cpu)
inst_dsp = ModuleInstance(name="dsp", module=dsp)
inst_mem = ModuleInstance(
    name="mem",
    module=mem,
    parameters={
        mem.parameters[0]._id: ElaboratableValue("8"),
        mem.parameters[1]._id: ElaboratableValue(0xFFFF),
    },
)

extp = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="o_wb_cyc", direction=PortDirection.IN),
    Port(name="o_wb_stb", direction=PortDirection.IN),
    Port(
        name="o_wb_adr",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("31"))]),
    ),
    Port(
        name="o_wb_dat",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("7"))]),
    ),
    Port(name="o_wb_we", direction=PortDirection.IN),
    Port(
        name="i_wb_dat",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue("7"))]),
    ),
    Port(name="i_wb_ack", direction=PortDirection.OUT),
    Port(name="i_wb_stall", direction=PortDirection.OUT),
    Port(name="i_wb_err", direction=PortDirection.OUT),
]
exti = [
    Interface(
        name="ext_manager",
        mode=InterfaceMode.SUBORDINATE,
        definition=wishbone,
        signals={
            wishbone.signals[0]._id: ReferencedPort.external(extp[2]),
            wishbone.signals[1]._id: ReferencedPort.external(extp[3]),
            wishbone.signals[2]._id: ReferencedPort.external(extp[8]),
            wishbone.signals[3]._id: ReferencedPort.external(extp[5]),
            wishbone.signals[4]._id: ReferencedPort.external(extp[7]),
            wishbone.signals[5]._id: ReferencedPort.external(extp[4]),
            wishbone.signals[6]._id: ReferencedPort.external(extp[6]),
            wishbone.signals[7]._id: ReferencedPort.external(extp[9]),
            wishbone.signals[8]._id: ReferencedPort.external(extp[10]),
        },
    )
]
top = Module(
    id=Identifier(name="top"),
    ports=extp,
    interfaces=exti,
    design=Design(
        components=[inst_cpu, inst_dsp, inst_mem],
        connections=[
            PortConnection(
                source=ReferencedPort(instance=inst_cpu, io=cpu.ports[0]),
                target=ReferencedPort.external(extp[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_cpu, io=cpu.ports[1]),
                target=ReferencedPort.external(extp[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_dsp, io=dsp.ports[0]),
                target=ReferencedPort.external(extp[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_dsp, io=dsp.ports[1]),
                target=ReferencedPort.external(extp[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_mem, io=mem.ports[0]),
                target=ReferencedPort.external(extp[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_mem, io=mem.ports[1]),
                target=ReferencedPort.external(extp[1]),
            ),
        ],
        interconnects=[
            WishboneInterconnect(
                name="wishbone_bus",
                clock=ReferencedPort.external(extp[0]),
                reset=ReferencedPort.external(extp[1]),
                params=WishboneRRParams(
                    addr_width=ElaboratableValue(32),
                    data_width=ElaboratableValue(8),
                    granularity=8,
                    features={WishboneRRFeature.ERR, WishboneRRFeature.STALL},
                ),
                managers={
                    ReferencedInterface(
                        instance=inst_cpu, io=cpu.interfaces[0]
                    )._id: WishboneRRManagerParams(),
                    ReferencedInterface.external(exti[0])._id: WishboneRRManagerParams(),
                },
                subordinates={
                    ReferencedInterface(
                        instance=inst_dsp, io=dsp.interfaces[0]
                    )._id: WishboneRRSubordinateParams(
                        address=ElaboratableValue(0), size=ElaboratableValue(0xFFFF)
                    ),
                    ReferencedInterface(
                        instance=inst_mem, io=mem.interfaces[0]
                    )._id: WishboneRRSubordinateParams(
                        address=ElaboratableValue(0x10000), size=ElaboratableValue(0xFF)
                    ),
                },
            )
        ],
    ),
)
