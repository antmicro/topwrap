import re

from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bit
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import Identifier

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
            name="dat_ms",
            type=Bit(),
            regexp=re.compile("dat_ms|mosi"),
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
            name="dat_sm",
            type=Bit(),
            regexp=re.compile("dat_sm|miso"),
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
            name="stall",
            type=Bit(),
            regexp=re.compile("stall"),
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
            name="err",
            type=Bit(),
            regexp=re.compile("err"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
            },
        ),
    ],
)
