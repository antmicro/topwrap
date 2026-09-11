# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import sys
from pathlib import Path

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.common import LayerType
from topwrap.cli import load_interfaces_from_repos
from topwrap.frontend.frontend import FrontendApproach
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.model.inference.inference import infer_interfaces_from_module
from topwrap.util import collect_filelist_sources

HERE = Path(__file__).resolve().parent
CALIPTRA_PATH = HERE / "Caliptra"

logging.basicConfig(level="INFO")

if len(sys.argv) < 2:
    print("Missing argument: top module")
    sys.exit(1)

top = sys.argv[1]

SV_SOURCES, INCLUDE_DIRS = collect_filelist_sources(
    CALIPTRA_PATH,
    base_sources=(CALIPTRA_PATH / "src/uart/rtl").rglob("*.sv") if top == "uart" else (),
)

modules = {
    m.id.name: m
    for m in SystemVerilogFrontend(approach=FrontendApproach.BEST_EFFORT, skip_selects=True)
    .parse_files(SV_SOURCES, include_dirs=INCLUDE_DIRS)
    .modules
}

[*intf_defs] = load_interfaces_from_repos()

for mod in modules[top].hierarchy():
    infer_interfaces_from_module(
        mod,
        intf_defs,
        grouping_hints={},
    )


kpm = KpmBackend(
    depth=-1,
    disabled_layers=[
        LayerType.IDENT.value,
    ],
    merge_ports_into_intfs=True,
)
out = kpm.represent(modules[top])

with open("./kpm_spec.json", "w") as s, open("./kpm_dataflow.json", "w") as d:
    json.dump(out.dataflow, d)
    json.dump(out.specification, s)
