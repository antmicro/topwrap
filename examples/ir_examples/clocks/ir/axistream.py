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

axi_stream = InterfaceDefinition(
    id=Identifier(name="AXI 4 Stream", vendor="amba.com", library="AMBA4"),
    signals=[
        InterfaceSignal(
            name="TVALID",
            type=Bit(),
            regexp=re.compile("tvalid"),
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
            name="TREADY",
            type=Bit(),
            regexp=re.compile("tready"),
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
            name="TDATA",
            type=Bit(),
            regexp=re.compile("tdata"),
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
            name="TKEEP",
            type=Bit(),
            regexp=re.compile("tkeep"),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT, required=False
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.IN, required=False
                ),
            },
        ),
        # and so on......
    ],
)
