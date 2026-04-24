# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from functools import cached_property
from typing import Dict, List

import marshmallow_dataclass

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    RegexpT,
    ext_field,
    flatten_and_annotate,
)
from topwrap.model.connections import PortDirection
from topwrap.model.misc import Identifier
from topwrap.util import recursive_defaultdict


class InterfaceModeDescription(Enum):
    MANAGER = "manager"
    SUBORDINATE = "subordinate"
    UNSPECIFIED = "unspecified"


class InterfaceSignalTypeDescription(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


@marshmallow_dataclass.dataclass(frozen=True)
class IfacePortSpecificationDescription(MarshmallowDataclassExtensions):
    """Specification of a port in an interface described in YAML interface definition file"""

    name: str
    regexp: RegexpT
    direction: PortDirection = ext_field(by_value=True)
    type: InterfaceSignalTypeDescription = ext_field(by_value=True)


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinitionSignalsDescription(MarshmallowDataclassExtensions):
    @marshmallow_dataclass.dataclass(frozen=True)
    class Inner:
        input: Dict[str, RegexpT] = ext_field(dict, data_key="in")
        output: Dict[str, RegexpT] = ext_field(dict, data_key="out")
        inout: Dict[str, RegexpT] = ext_field(dict)

    required: Inner = ext_field(Inner)
    optional: Inner = ext_field(Inner)

    @cached_property
    def flat(self) -> List[IfacePortSpecificationDescription]:
        return [
            IfacePortSpecificationDescription.from_dict(port)
            for port in flatten_and_annotate(
                self.to_dict(), ["type", "direction", "name", "regexp"]
            )
        ]

    @staticmethod
    def from_flat(
        arr: List[IfacePortSpecificationDescription],
    ) -> "InterfaceDefinitionSignalsDescription":
        data = recursive_defaultdict()
        for sig in arr:
            data[sig.type.value][sig.direction.value][sig.name] = sig.regexp
        return InterfaceDefinitionSignalsDescription.from_dict(data)


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinitionDescription(MarshmallowDataclassExtensions):
    """Interface described in YAML interface definition file"""

    id: Identifier
    signals: InterfaceDefinitionSignalsDescription = ext_field(
        InterfaceDefinitionSignalsDescription
    )

    @cached_property
    def optional_signals(self) -> List[IfacePortSpecificationDescription]:
        return list(
            filter(
                lambda sig: sig.type == InterfaceSignalTypeDescription.OPTIONAL, self.signals.flat
            )
        )

    @cached_property
    def required_signals(self) -> List[IfacePortSpecificationDescription]:
        return list(
            filter(
                lambda sig: sig.type == InterfaceSignalTypeDescription.REQUIRED, self.signals.flat
            )
        )
