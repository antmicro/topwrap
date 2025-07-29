import re
from typing import Optional

from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bit, Bits, BitStruct, Dimensions, StructField
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier


def algostring(len: int):
    return Bits(
        dimensions=[
            Dimensions(upper=ElaboratableValue(len - 1)),
            Dimensions(upper=ElaboratableValue(7)),
        ],
    )


AnonControlStruct = BitStruct(
    fields=[StructField(name="full", type=Bit()), StructField(name="forward", type=Bit())]
)


def make_mm(mreq: bool, dir: PortDirection, sreq: Optional[bool] = None):
    return {
        InterfaceMode.MANAGER: InterfaceSignalConfiguration(direction=dir, required=mreq),
        InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
            direction=dir.reverse(), required=mreq if sreq is None else sreq
        ),
    }


sci_intf = InterfaceDefinition(
    id=Identifier(name="Simply Complex Interface 4", vendor="top.wrap", library="scilib"),
    signals=[
        InterfaceSignal(
            name="addr",
            regexp=re.compile("addr"),
            type=Bits(dimensions=[Dimensions(ElaboratableValue("32-1"))]),
            modes=make_mm(True, PortDirection.OUT),
        ),
        InterfaceSignal(
            name="write",
            regexp=re.compile("write"),
            type=Bit(),
            modes=make_mm(True, PortDirection.OUT),
        ),
        InterfaceSignal(
            name="strb",
            regexp=re.compile("strb"),
            type=Bits(dimensions=[Dimensions(ElaboratableValue("64/8-1"))]),
            modes=make_mm(True, PortDirection.OUT),
        ),
        InterfaceSignal(
            name="ack",
            regexp=re.compile("ack"),
            type=Bit(),
            modes=make_mm(True, PortDirection.OUT),
        ),
        InterfaceSignal(
            name="rdata",
            regexp=re.compile("(rdata)|(idata)"),
            type=Bits(dimensions=[Dimensions(ElaboratableValue("64-1"))]),
            default=ElaboratableValue(0),
            modes=make_mm(True, PortDirection.IN, False),
        ),
        InterfaceSignal(
            name="wdata",
            regexp=re.compile("(wdata)|(odata)"),
            type=Bits(dimensions=[Dimensions(ElaboratableValue("64-1"))]),
            default=ElaboratableValue(0),
            modes=make_mm(False, PortDirection.OUT, False),
        ),
        InterfaceSignal(
            name="sack",
            regexp=re.compile("(sack|s_ack)"),
            type=Bits(dimensions=[Dimensions(ElaboratableValue(1))]),
            modes=make_mm(True, PortDirection.IN),
        ),
    ],
)
