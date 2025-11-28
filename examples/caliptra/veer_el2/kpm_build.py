# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.util import collect_filelist_sources

HERE = Path(__file__).resolve().parent
CALIPTRA_PATH = HERE / "../Caliptra"

SV_SOURCES, INCLUDE_DIRS = collect_filelist_sources(CALIPTRA_PATH)

modules = {
    m.id.name: m
    for m in SystemVerilogFrontend().parse_files(SV_SOURCES, include_dirs=INCLUDE_DIRS).modules
}

kpm = KpmBackend(depth=-1)
out = kpm.represent(modules["el2_veer"])

with open("./kpm_spec.json", "w") as s, open("./kpm_dataflow.json", "w") as d:
    json.dump(out.dataflow, d)
    json.dump(out.specification, s)
