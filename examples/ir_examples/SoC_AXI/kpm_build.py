# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json

from ir.design import top

from topwrap.backend.kpm.backend import KpmBackend

out = KpmBackend(depth=-1).represent(top)

with open("./kpm_spec.json", "w") as s, open("./kpm_dataflow.json", "w") as d:
    json.dump(out.dataflow, d)
    json.dump(out.specification, s)
