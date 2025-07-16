# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

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

params = {
    "id_width": 3,
    "addr": 32,
    "data": 64,
}

axi_signals = [
    ("aw", "id", False, params["id_width"]),
    ("aw", "addr", False, params["addr"]),
    ("aw", "len", False, 8),
    ("aw", "size", False, 3),
    ("aw", "burst", False, 2),
    ("aw", "lock", False, 0),
    ("aw", "cache", False, 4),
    ("aw", "prot", False, 3),
    ("aw", "region", False, 4),
    ("aw", "qos", False, 4),
    ("aw", "valid", False, 0),
    ("aw", "ready", True, 0),
    ("ar", "id", False, params["id_width"]),
    ("ar", "addr", False, params["addr"]),
    ("ar", "len", False, 8),
    ("ar", "size", False, 3),
    ("ar", "burst", False, 2),
    ("ar", "lock", False, 0),
    ("ar", "cache", False, 4),
    ("ar", "prot", False, 3),
    ("ar", "region", False, 4),
    ("ar", "qos", False, 4),
    ("ar", "valid", False, 0),
    ("ar", "ready", True, 0),
    ("w", "data", False, params["data"]),
    ("w", "strb", False, params["data"] // 8),
    ("w", "last", False, 0),
    ("w", "valid", False, 0),
    ("w", "ready", True, 0),
    ("b", "id", True, params["id_width"]),
    ("b", "resp", True, 2),
    ("b", "valid", True, 0),
    ("b", "ready", False, 0),
    ("r", "id", True, params["id_width"]),
    ("r", "data", True, params["data"]),
    ("r", "resp", True, 2),
    ("r", "last", True, 0),
    ("r", "valid", True, 0),
    ("r", "ready", False, 0),
]

signals = []

for ch, name, direction, width in axi_signals:
    signals.append(
        InterfaceSignal(
            name=f"{ch}{name}",
            type=Bit()
            if width == 0
            else Bits(dimensions=[Dimensions(upper=ElaboratableValue(width - 1))]),
            regexp=re.compile(name),
            modes={
                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                    direction=PortDirection.IN if direction else PortDirection.OUT, required=True
                ),
                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                    direction=PortDirection.OUT if direction else PortDirection.IN, required=True
                ),
            },
        )
    )

interconnect_axi = InterfaceDefinition(
    id=Identifier(name="AXI"),
    signals=signals,
)
