# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from typing import Dict

import marshmallow_dataclass

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    RegexpT,
    ext_field,
)
from topwrap.model.misc import Identifier


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
    signals: InterfaceDefinitionSignalsDescription = ext_field(
        InterfaceDefinitionSignalsDescription
    )
