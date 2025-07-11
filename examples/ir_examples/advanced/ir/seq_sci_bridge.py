from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .types import AnonControlStruct, sci_intf

external_ports = [
    Port(
        name="byte",
        direction=PortDirection.IN,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(7))]),
    ),
    Port(name="control", direction=PortDirection.INOUT, type=AnonControlStruct),
]

signals = {s._id: None for s in sci_intf.signals}
del signals[sci_intf.signals.efind_by_name("rdata")._id]

seq_sci_mod = Module(
    id=Identifier(name="seq_to_sci4_bridge", vendor="top.wrap", library="scilib"),
    ports=external_ports,
    interfaces=[
        Interface(name="SCI", mode=InterfaceMode.SUBORDINATE, definition=sci_intf, signals=signals)
    ],
)
