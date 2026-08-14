# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Dict, Literal, Optional

import marshmallow
import marshmallow_dataclass

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    RegexpT,
    ext_field,
)
from topwrap.model.misc import Identifier

InterfaceDefinitionSignalDirection = Literal["in", "out", "inout"]
InterfaceDefinitionSignalRequired = Literal["required", "optional"]
InterfaceDefinitionSignalMode = tuple[
    InterfaceDefinitionSignalDirection, InterfaceDefinitionSignalRequired
]


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinitionSignalDescription(MarshmallowDataclassExtensions):
    pattern: RegexpT = ext_field()
    modes: dict[str, InterfaceDefinitionSignalMode] = ext_field()
    default: Optional[str | int] = ext_field(None)

    @marshmallow.validates_schema
    def _validate(self, self_obj: Dict[str, Any], **kwargs: Any) -> bool:
        if not self_obj["modes"]:
            raise marshmallow.ValidationError("Interface signal needs at least one mode")

        return True


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinitionSignalsDescription(MarshmallowDataclassExtensions):
    @marshmallow_dataclass.dataclass(frozen=True)
    class Inner:
        input: Dict[str, RegexpT] = ext_field(dict, data_key="in")
        output: Dict[str, RegexpT] = ext_field(dict, data_key="out")
        inout: Dict[str, RegexpT] = ext_field(dict)

    required: Inner = ext_field(Inner)
    optional: Inner = ext_field(Inner)


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinitionDescription(MarshmallowDataclassExtensions):
    """Interface described in YAML interface definition file"""

    id: Identifier
    signals: (
        InterfaceDefinitionSignalsDescription | dict[str, InterfaceDefinitionSignalDescription]
    ) = ext_field(inline_depth=2)
