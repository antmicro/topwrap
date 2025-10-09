# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from enum import Enum

import marshmallow_dataclass

from topwrap.model.interconnect import (
    Interconnect,
    InterconnectManagerParams,
    InterconnectParams,
    InterconnectSubordinateParams,
)
from topwrap.model.misc import ElaboratableValue


class AXIFeature(Enum):
    pass


@marshmallow_dataclass.dataclass
class AXIParams(InterconnectParams):
    atop: bool


@marshmallow_dataclass.dataclass
class AXIManagerParams(InterconnectManagerParams):
    id_width: ElaboratableValue.Field


@marshmallow_dataclass.dataclass
class AXISubordinateParams(InterconnectSubordinateParams):
    pass


class AXIInterconnect(Interconnect[AXIParams, AXIManagerParams, AXISubordinateParams]):
    pass
