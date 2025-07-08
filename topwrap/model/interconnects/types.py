from dataclasses import dataclass
from typing import Type

from topwrap.model.interconnect import (
    Interconnect,
    InterconnectManagerParams,
    InterconnectParams,
    InterconnectSubordinateParams,
)
from topwrap.model.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRManagerParams,
    WishboneRRParams,
    WishboneRRSubordinateParams,
)


@dataclass
class InterconnectTypeInfo:
    intercon: Type[Interconnect]
    params: Type[InterconnectParams]
    man_params: Type[InterconnectManagerParams]
    sub_params: Type[InterconnectSubordinateParams]


INTERCONNECT_TYPES: dict[str, InterconnectTypeInfo] = {
    "Wishbone Round-Robin": InterconnectTypeInfo(
        WishboneInterconnect,
        WishboneRRParams,
        WishboneRRManagerParams,
        WishboneRRSubordinateParams,
    )
}
