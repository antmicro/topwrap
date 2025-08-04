import re

from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bit, Bits, Dimensions
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier

wishbone = InterfaceDefinition(
    id=Identifier(name="wishbone"),
    signals=[
        InterfaceSignal(
            name="cyc",
            type=Bit(),
            regexp=re.compile("cyc"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=True
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=True
                ),
            },
        ),
        InterfaceSignal(
            name="stb",
            type=Bit(),
            regexp=re.compile("stb"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=True
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=True
                ),
            },
        ),
        InterfaceSignal(
            name="ack",
            type=Bit(),
            regexp=re.compile("ack"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=True
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=True
                ),
            },
        ),
        InterfaceSignal(
            name="dat_w",
            type=Bit(),
            regexp=re.compile("dat_w|mosi"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
        InterfaceSignal(
            name="dat_r",
            type=Bit(),
            regexp=re.compile("dat_r|miso"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
            },
        ),
        InterfaceSignal(
            name="adr",
            type=Bit(),
            regexp=re.compile("adr"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
        InterfaceSignal(
            name="we",
            type=Bit(),
            regexp=re.compile("we"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
        InterfaceSignal(
            name="bte",
            type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(1))]),
            regexp=re.compile("bte"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
        InterfaceSignal(
            name="cti",
            type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(2))]),
            regexp=re.compile("cti"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
        InterfaceSignal(
            name="sel",
            type=Bits(dimensions=[Dimensions(upper=ElaboratableValue(3))]),
            regexp=re.compile("sel"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
    ],
)
