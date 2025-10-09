# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Type

from topwrap.interconnects.axi import (
    AXIInterconnect,
    AXIManagerParams,
    AXIParams,
    AXISubordinateParams,
)
from topwrap.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRManagerParams,
    WishboneRRParams,
    WishboneRRSubordinateParams,
)
from topwrap.model.interconnect import (
    Interconnect,
    InterconnectManagerParams,
    InterconnectParams,
    InterconnectSubordinateParams,
)


@dataclass
class InterconnectTypeInfo:
    intercon: Type[Interconnect]
    params: Type[InterconnectParams]
    man_params: Type[InterconnectManagerParams]
    sub_params: Type[InterconnectSubordinateParams]


#: Maps name to specific interconnect implementation. Used by YAML frontend.
INTERCONNECT_TYPES: dict[str, InterconnectTypeInfo] = {
    "Wishbone Round-Robin": InterconnectTypeInfo(
        WishboneInterconnect,
        WishboneRRParams,
        WishboneRRManagerParams,
        WishboneRRSubordinateParams,
    ),
    "AXI": InterconnectTypeInfo(
        AXIInterconnect,
        AXIParams,
        AXIManagerParams,
        AXISubordinateParams,
    ),
}
