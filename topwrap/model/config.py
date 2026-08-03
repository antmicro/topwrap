# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import marshmallow_dataclass
from typing_extensions import Optional

from topwrap.common_serdes import MarshmallowDataclassExtensions, ResourcePathT, ext_field


@marshmallow_dataclass.dataclass
class ConfigDescription(MarshmallowDataclassExtensions):
    """Global topwrap configuration"""

    force_interface_compliance: Optional[bool] = ext_field(False)
    repositories: dict[str, ResourcePathT] = ext_field(dict)
