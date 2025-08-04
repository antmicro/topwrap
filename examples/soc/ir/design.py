from topwrap.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRFeature,
    WishboneRRManagerParams,
    WishboneRRParams,
    WishboneRRSubordinateParams,
)
from topwrap.model.connections import (
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .crg import crg
from .mem import mem
from .uart import uart
from .vex_riscv import vex_riscv

inst_mem_data = ModuleInstance(
    name="mem_data",
    module=mem,
    parameters={
        mem.parameters[0]._id: ElaboratableValue("'h1000"),
    },
)
inst_mem_instr = ModuleInstance(
    name="mem_instr",
    module=mem,
    parameters={
        mem.parameters[0]._id: ElaboratableValue("'hA000"),
        mem.parameters[1]._id: ElaboratableValue('"build/bios.init"'),
    },
)
inst_uart = ModuleInstance(
    name="uart",
    module=uart,
)
inst_crg = ModuleInstance(name="crg", module=crg)
inst_cpu = ModuleInstance(name="cpu", module=vex_riscv)

extp = [
    Port(name="clk100", direction=PortDirection.IN),
    Port(name="serial_rx", direction=PortDirection.IN),
    Port(name="serial_tx", direction=PortDirection.OUT),
]

design = Design(
    components=[inst_mem_data, inst_mem_instr, inst_uart, inst_cpu, inst_crg],
    connections=[
        PortConnection(
            source=ReferencedPort(instance=inst_crg, io=crg.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_mem_data, io=mem.ports[1]),
            target=ReferencedPort(instance=inst_crg, io=crg.ports[2]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_mem_data, io=mem.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_mem_instr, io=mem.ports[1]),
            target=ReferencedPort(instance=inst_crg, io=crg.ports[2]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_mem_instr, io=mem.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart, io=uart.ports[1]),
            target=ReferencedPort(instance=inst_crg, io=crg.ports[2]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart, io=uart.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart, io=uart.ports[13]),
            target=ReferencedPort.external(extp[1]),  # RX
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_uart, io=uart.ports[12]),
            target=ReferencedPort.external(extp[2]),  # TX
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_cpu, io=vex_riscv.ports[0]),
            target=ReferencedPort.external(extp[0]),
        ),
        PortConnection(
            source=ReferencedPort(instance=inst_cpu, io=vex_riscv.ports[1]),
            target=ReferencedPort(instance=inst_crg, io=crg.ports[2]),
        ),
    ],
    interconnects=[
        WishboneInterconnect(
            name="wishbone_bus",
            clock=ReferencedPort.external(extp[0]),
            reset=ReferencedPort(instance=inst_crg, io=crg.ports[2]),
            params=WishboneRRParams(
                addr_width=ElaboratableValue(30),
                data_width=ElaboratableValue(32),
                granularity=8,
                features={WishboneRRFeature.CTI, WishboneRRFeature.BTE},
            ),
            managers={
                ReferencedInterface(
                    instance=inst_cpu, io=vex_riscv.interfaces[0]
                )._id: WishboneRRManagerParams(),
                ReferencedInterface(
                    instance=inst_cpu, io=vex_riscv.interfaces[1]
                )._id: WishboneRRManagerParams(),
            },
            subordinates={
                ReferencedInterface(
                    instance=inst_mem_data, io=mem.interfaces[0]
                )._id: WishboneRRSubordinateParams(
                    address=ElaboratableValue(0), size=ElaboratableValue(0xA000)
                ),
                ReferencedInterface(
                    instance=inst_mem_instr, io=mem.interfaces[0]
                )._id: WishboneRRSubordinateParams(
                    address=ElaboratableValue(0x10000000), size=ElaboratableValue(0x1000)
                ),
                ReferencedInterface(
                    instance=inst_uart, io=uart.interfaces[0]
                )._id: WishboneRRSubordinateParams(
                    address=ElaboratableValue(0xF0000000), size=ElaboratableValue(0x1000)
                ),
            },
        )
    ],
)

top = Module(
    id=Identifier(name="simple_soc"),
    ports=extp,
    design=design,
)
