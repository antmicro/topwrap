# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.frontend.sv.frontend import SystemVerilogFrontend

HERE = Path(__file__).resolve().parent
SV_SOURCES = [HERE / "verilogs" / "hierarchy.v"]

modules = {m.id.name: m for m in SystemVerilogFrontend().parse_files(SV_SOURCES).modules}
kpm = KpmBackend(depth=-1)
out = kpm.represent(modules["A"])

# for docs
with open("./kpm_spec.json", "w") as s, open("./kpm_dataflow.json", "w") as d:
    json.dump(out.dataflow, d)
    json.dump(out.specification, s)

# for tests
(HERE / "kpm_spec.json").write_text(json.dumps(out.specification))
(HERE / "kpm_dataflow.json").write_text(json.dumps(out.dataflow))
