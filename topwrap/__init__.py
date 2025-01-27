# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import os

if (var := "AMARANTH_USE_YOSYS") not in os.environ:
    os.environ[var] = "builtin"
