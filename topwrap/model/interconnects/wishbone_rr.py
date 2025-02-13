# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from topwrap.model.interconnect import (
    Interconnect,
    InterconnectManagerParams,
    InterconnectParams,
    InterconnectSubordinateParams,
)
from topwrap.model.misc import ElaboratableValue


class WishboneRRFeature(Enum):
    ERR = "err"
    RTY = "rty"
    STALL = "stall"
    LOCK = "lock"
    CTI = "cti"
    BTE = "bte"


@dataclass
class WishboneRRParams(InterconnectParams):
    #: Bit width of the address line (addresses access data_width-sized chunks)
    data_width: ElaboratableValue.Field

    #: Bit width of the data line
    addr_width: ElaboratableValue.Field

    #: Access granularity - the smallest unit of data transfer that the interconnect can transfer
    granularity: Literal[8, 16, 32, 64]

    #: set of optional wishbone signals that the interconnect should implement
    features: set[WishboneRRFeature]


@dataclass
class WishboneRRManagerParams(InterconnectManagerParams):
    pass


@dataclass
class WishboneRRSubordinateParams(InterconnectSubordinateParams):
    pass


class WishboneInterconnect(
    Interconnect[WishboneRRParams, WishboneRRManagerParams, WishboneRRSubordinateParams]
):
    """
    This interconnect only supports Wishbone interfaces for managers and subordinates.
    It supports multiple managers, but only one of them can drive the bus at a time
    (i.e. only one transaction can be happening on the bus at any given moment).
    A round-robin arbiter decides which manager can currently drive the bus.

    The currently known limitations are:
        - Only word-sized addressing is supported (in other words - consecutive
            addresses can only access word-sized chunks of data)
        - Crossing clock domains, down-converting (initiating multiple transactions
            on a narrow bus per one transaction on a wider bus) and up-converting are not supported
    """
