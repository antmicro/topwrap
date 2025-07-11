from typing import cast

from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import (
    Bits,
    BitStruct,
    Dimensions,
    LogicBitSelect,
    LogicFieldSelect,
    LogicSelect,
    StructField,
)
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

from .proc import proc_mod
from .seq_sci_bridge import seq_sci_mod
from .sseq import sseq_mod
from .types import algostring, sci_intf

sseq = ModuleInstance(name="sseq", module=sseq_mod)
seq_to_sci = ModuleInstance(name="seq_to_sci", module=seq_sci_mod)
proc = ModuleInstance(name="proc", module=proc_mod)

external_ports = [
    Port(
        name="char_streams",
        direction=PortDirection.IN,
        type=BitStruct(
            name="stream_struct",
            fields=[
                a_strf := StructField(name="a_stream", type=algostring(64)),
                b_strf := StructField(name="b_stream", type=algostring(64)),
            ],
        ),
    ),
    Port(
        name="cow_out",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(7))]),
    ),
    Port(
        name="hw_id",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
    ),
    Port(name="clk", direction=PortDirection.IN),
]

sci_sigs = {s._id: None for s in sci_intf.signals}
del sci_sigs[sci_intf.signals.find_by_name_or_error("wdata")._id]

module = Module(
    id=Identifier(name="advanced_top"),
    ports=external_ports,
    interfaces=[
        sci_ctrl_inst := Interface(
            name="SCI_ctrl",
            definition=sci_intf,
            mode=InterfaceMode.SUBORDINATE,
            signals=sci_sigs,
        ),
        sci_extcon_man := Interface(
            name="SCI_ext_man",
            definition=sci_intf,
            mode=InterfaceMode.MANAGER,
            signals={s._id: None for s in sci_intf.signals},
        ),
        sci_extcon_sub := Interface(
            name="SCI_ext_sub",
            definition=sci_intf,
            mode=InterfaceMode.SUBORDINATE,
            signals={s._id: None for s in sci_intf.signals},
        ),
    ],
    parameters=[
        Parameter(name="CIF_ADDR_WIDTH", default_value=ElaboratableValue(32)),
        Parameter(name="CIF_DATA_WIDTH", default_value=ElaboratableValue(64)),
    ],
    design=Design(
        components=[sseq, seq_to_sci, proc],
        connections=[
            ConstantConnection(
                source=ElaboratableValue(0x34256), target=ReferencedPort.external(external_ports[2])
            ),
            PortConnection(
                source=ReferencedPort.external(
                    io=external_ports[0],
                    select=LogicSelect(
                        logic=external_ports[0].type, ops=[LogicFieldSelect(a_strf)]
                    ),
                ),
                target=ReferencedPort(
                    instance=sseq,
                    io=(port := sseq_mod.ports.find_by_name_or_error("str")),
                    select=LogicSelect(
                        logic=port.type,
                        ops=[
                            LogicBitSelect(
                                Dimensions(ElaboratableValue(127), ElaboratableValue(64))
                            )
                        ],
                    ),
                ),
            ),
            PortConnection(
                source=ReferencedPort.external(
                    io=external_ports[0],
                    select=LogicSelect(
                        logic=external_ports[0].type, ops=[LogicFieldSelect(b_strf)]
                    ),
                ),
                target=ReferencedPort(
                    instance=sseq,
                    io=(port := sseq_mod.ports.find_by_name_or_error("str")),
                    select=LogicSelect(
                        logic=port.type,
                        ops=[
                            LogicBitSelect(Dimensions(ElaboratableValue(63), ElaboratableValue(0)))
                        ],
                    ),
                ),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=sseq, io=sseq_mod.ports.find_by_name_or_error("byte")
                ),
                target=ReferencedPort(
                    instance=seq_to_sci, io=seq_sci_mod.ports.find_by_name_or_error("byte")
                ),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=sseq, io=sseq_mod.ports.find_by_name_or_error("control")
                ),
                target=ReferencedPort(
                    instance=seq_to_sci, io=seq_sci_mod.ports.find_by_name_or_error("control")
                ),
            ),
            InterfaceConnection(
                source=ReferencedInterface(
                    instance=seq_to_sci, io=seq_sci_mod.interfaces.find_by_name_or_error("SCI")
                ),
                target=ReferencedInterface(
                    instance=proc, io=proc_mod.interfaces.find_by_name_or_error("SCI")
                ),
            ),
            PortConnection(
                source=ReferencedPort(
                    instance=proc,
                    io=(port := proc_mod.ports.find_by_name_or_error("cows")),
                    select=LogicSelect(
                        logic=port.type,
                        ops=[LogicFieldSelect(cast(BitStruct, port.type).fields[0])],
                    ),
                ),
                target=ReferencedPort.external(io=external_ports[1]),
            ),
            InterfaceConnection(
                source=ReferencedInterface.external(sci_ctrl_inst),
                target=ReferencedInterface(
                    instance=proc,
                    io=proc_mod.interfaces.find_by_name_or_error("externally_controlled_SCI"),
                ),
            ),
            PortConnection(
                source=ReferencedPort.external(io=external_ports[-1]),
                target=ReferencedPort(
                    instance=proc, io=proc_mod.ports.find_by_name_or_error("clk")
                ),
            ),
            InterfaceConnection(
                source=ReferencedInterface.external(sci_extcon_man),
                target=ReferencedInterface.external(sci_extcon_sub),
            ),
        ],
    ),
)
