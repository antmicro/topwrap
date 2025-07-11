from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .types import AnonControlStruct, algostring

external_ports = [
    Port(name="str", direction=PortDirection.IN, type=algostring(128)),
    Port(
        name="byte",
        direction=PortDirection.OUT,
        type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(7))]),
    ),
    Port(name="control", direction=PortDirection.INOUT, type=AnonControlStruct),
]

sseq_mod = Module(
    id=Identifier(name="string_sequencer", vendor="top.wrap", library="advlib"),
    ports=external_ports,
)
