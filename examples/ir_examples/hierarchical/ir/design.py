from topwrap.model.connections import (
    Port,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import LogicSlice
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .adder import adder
from .d_ff import d_ff
from .debouncer import debouncer

encoder = Module(
    id=Identifier(name="encoder"),
    ports=[
        Port(name="number", direction=PortDirection.IN),
        Port(name="clk", direction=PortDirection.IN),
        Port(name="enc0", direction=PortDirection.OUT),
        Port(name="enc1", direction=PortDirection.OUT),
        Port(name="enc2", direction=PortDirection.OUT),
    ],
    design=Design(),
)


bitcnt4ext = [
    Port(name="impulse", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="sum", direction=PortDirection.OUT),
]
inst_dff = ModuleInstance(name="D-flipflop", module=d_ff)
inst_adder = ModuleInstance(name="adder", module=adder)
bitcnt4 = Module(
    id=Identifier(name="4-bit counter"),
    ports=bitcnt4ext,
    design=Design(
        components=[inst_adder, inst_dff],
        connections=[
            PortConnection(
                source=ReferencedPort(instance=inst_dff, io=LogicSlice(logic=d_ff.ports[2].type)),
                target=ReferencedPort(
                    instance=inst_adder, io=LogicSlice(logic=adder.ports[2].type)
                ),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_dff, io=LogicSlice(logic=d_ff.ports[3].type)),
                target=ReferencedPort.external(LogicSlice(logic=bitcnt4ext[2].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_dff, io=LogicSlice(logic=d_ff.ports[0].type)),
                target=ReferencedPort.external(LogicSlice(logic=bitcnt4ext[0].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_dff, io=LogicSlice(logic=d_ff.ports[1].type)),
                target=ReferencedPort.external(LogicSlice(logic=bitcnt4ext[1].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_adder, io=LogicSlice(logic=adder.ports[0].type)
                ),
                target=ReferencedPort(instance=inst_dff, io=LogicSlice(logic=d_ff.ports[3].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_adder, io=LogicSlice(logic=adder.ports[1].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=bitcnt4ext[0].type)),
            ),
        ],
    ),
)


proc_exts = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="btn", direction=PortDirection.IN),
    Port(name="enc0", direction=PortDirection.OUT),
    Port(name="enc1", direction=PortDirection.OUT),
    Port(name="enc2", direction=PortDirection.OUT),
]
inst_deb = ModuleInstance(name="debouncer", module=debouncer)
inst_4bc = ModuleInstance(name="4-bit counter", module=bitcnt4)
inst_enc = ModuleInstance(name="encoder", module=encoder)
proc = Module(
    id=Identifier(name="proc"),
    ports=proc_exts,
    design=Design(
        components=[inst_deb, inst_4bc, inst_enc],
        connections=[
            PortConnection(
                source=ReferencedPort(
                    instance=inst_4bc, io=LogicSlice(logic=bitcnt4.ports[0].type)
                ),
                target=ReferencedPort(
                    instance=inst_deb, io=LogicSlice(logic=debouncer.ports[2].type)
                ),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_4bc, io=LogicSlice(logic=bitcnt4.ports[1].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[1].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_deb, io=LogicSlice(logic=debouncer.ports[0].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[0].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_deb, io=LogicSlice(logic=debouncer.ports[1].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[2].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_enc, io=LogicSlice(logic=encoder.ports[1].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[0].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_enc, io=LogicSlice(logic=encoder.ports[2].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[3].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_enc, io=LogicSlice(logic=encoder.ports[3].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[4].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_enc, io=LogicSlice(logic=encoder.ports[4].type)
                ),
                target=ReferencedPort.external(LogicSlice(logic=proc_exts[5].type)),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=inst_enc, io=LogicSlice(logic=encoder.ports[0].type)
                ),
                target=ReferencedPort(
                    instance=inst_4bc, io=LogicSlice(logic=bitcnt4.ports[2].type)
                ),
            ),
        ],
    ),
)


top_ext = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="btn", direction=PortDirection.IN),
    Port(name="disp0", direction=PortDirection.OUT),
    Port(name="disp1", direction=PortDirection.OUT),
    Port(name="disp2", direction=PortDirection.OUT),
]
inst_proc = ModuleInstance(name="proc", module=proc)
top = Module(
    id=Identifier(name="top"),
    ports=top_ext,
    design=Design(
        components=[inst_proc],
        connections=[
            PortConnection(
                source=ReferencedPort(instance=inst_proc, io=LogicSlice(logic=proc.ports[2].type)),
                target=ReferencedPort.external(LogicSlice(logic=top_ext[2].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_proc, io=LogicSlice(logic=proc.ports[0].type)),
                target=ReferencedPort.external(LogicSlice(logic=top_ext[0].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_proc, io=LogicSlice(logic=proc.ports[1].type)),
                target=ReferencedPort.external(LogicSlice(logic=top_ext[1].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_proc, io=LogicSlice(logic=proc.ports[3].type)),
                target=ReferencedPort.external(LogicSlice(logic=top_ext[3].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_proc, io=LogicSlice(logic=proc.ports[4].type)),
                target=ReferencedPort.external(LogicSlice(logic=top_ext[4].type)),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_proc, io=LogicSlice(logic=proc.ports[5].type)),
                target=ReferencedPort.external(LogicSlice(logic=top_ext[5].type)),
            ),
        ],
    ),
)
