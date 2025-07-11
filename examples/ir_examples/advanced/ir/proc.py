from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    LogicFieldSelect,
    LogicSelect,
    StructField,
)
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .types import sci_intf

external_ports = [
    Port(
        name="sci_control",
        direction=PortDirection.OUT,
        type=BitStruct(
            fields=[
                sci_addr := StructField(
                    name="addr", type=Bits(dimensions=[Dimensions(ElaboratableValue(31))])
                ),
                sci_write := StructField(name="write", type=Bit()),
                sci_strb := StructField(
                    name="strb", type=Bits(dimensions=[Dimensions(ElaboratableValue(7))])
                ),
                sci_ack := StructField(name="ack", type=Bit()),
            ]
        ),
    ),
    Port(
        name="cows",
        direction=PortDirection.OUT,
        type=BitStruct(
            name="cow_struct",
            fields=[
                StructField(name="enc", type=Bits(dimensions=[Dimensions(ElaboratableValue(7))])),
                StructField(
                    name="length", type=Bits(dimensions=[Dimensions(ElaboratableValue(31))])
                ),
            ],
        ),
    ),
    (pack := Port(name="plain_ack", direction=PortDirection.IN, type=Bit())),
    (
        pwdata := Port(
            name="plain_wdata",
            direction=PortDirection.IN,
            type=Bits(dimensions=[Dimensions(ElaboratableValue(63))]),
        )
    ),
    (psack := Port(name="plain_sack", direction=PortDirection.OUT)),
    Port(name="clk", direction=PortDirection.IN),
]

proc_mod = Module(
    id=Identifier(name="char_processor", vendor="top.wrap", library="scilib"),
    ports=external_ports,
    interfaces=[
        Interface(
            name="SCI",
            mode=InterfaceMode.MANAGER,
            definition=sci_intf,
            signals={
                sci_intf.signals.find_by_name_or_error("addr")._id: ReferencedPort.external(
                    io=external_ports[0],
                    select=LogicSelect(
                        logic=external_ports[0].type, ops=[LogicFieldSelect(sci_addr)]
                    ),
                ),
                sci_intf.signals.find_by_name_or_error("write")._id: ReferencedPort.external(
                    io=external_ports[0],
                    select=LogicSelect(
                        logic=external_ports[0].type, ops=[LogicFieldSelect(sci_write)]
                    ),
                ),
                sci_intf.signals.find_by_name_or_error("strb")._id: ReferencedPort.external(
                    io=external_ports[0],
                    select=LogicSelect(
                        logic=external_ports[0].type, ops=[LogicFieldSelect(sci_strb)]
                    ),
                ),
                sci_intf.signals.find_by_name_or_error("ack")._id: ReferencedPort.external(
                    io=external_ports[0],
                    select=LogicSelect(
                        logic=external_ports[0].type, ops=[LogicFieldSelect(sci_ack)]
                    ),
                ),
                sci_intf.signals.find_by_name_or_error("rdata")._id: None,
                sci_intf.signals.find_by_name_or_error("wdata")._id: None,
                sci_intf.signals.find_by_name_or_error("sack")._id: None,
            },
        ),
        Interface(
            name="externally_controlled_SCI",
            mode=InterfaceMode.SUBORDINATE,
            definition=sci_intf,
            signals={
                **{s._id: None for s in sci_intf.signals},
                sci_intf.signals.find_by_name_or_error("ack")._id: ReferencedPort.external(pack),
                sci_intf.signals.find_by_name_or_error("wdata")._id: ReferencedPort.external(
                    pwdata
                ),
                sci_intf.signals.find_by_name_or_error("sack")._id: ReferencedPort.external(psack),
            },
        ),
    ],
)
