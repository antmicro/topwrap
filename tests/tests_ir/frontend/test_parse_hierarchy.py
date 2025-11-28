# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.tests_ir.shared.helpers import (
    canonical_flow,
    canonical_spec,
    get_caliptra_sources,
    normalize_sv,
)
from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.frontend.sv.frontend import SystemVerilogFrontend


@pytest.mark.parametrize(
    "sv_sources",
    [[Path("examples/ir_examples/parse_hierarchy/verilogs/hierarchy.v")]],
)
def test_parse_hierarchy_matches_golden_kpm(sv_sources):
    from examples.ir_examples.parse_hierarchy.golden_ir.design import A as top_module

    kpm = KpmBackend(depth=-1)
    kpm_out = kpm.represent(top_module)

    golden_spec = canonical_spec(kpm_out.specification)
    golden_flow = canonical_flow(kpm_out.dataflow)

    frontend = SystemVerilogFrontend()
    modules = {m.id.name: m for m in frontend.parse_files(sv_sources).modules}
    top = modules["A"]

    kpm_out = KpmBackend(depth=-1).represent(top)

    assert canonical_spec(kpm_out.specification) == golden_spec
    assert canonical_flow(kpm_out.dataflow) == golden_flow


def test_parse_hierarchy_sv_roundtrip(tmp_path: Path):
    sv_sources, include_dirs = get_caliptra_sources()
    frontend = SystemVerilogFrontend()
    modules = {
        m.id.name: m for m in frontend.parse_files(sv_sources, include_dirs=include_dirs).modules
    }
    for modname in modules:
        print("Verifying module:", modname, file=sys.stderr)
        top = modules[modname]

        backend = SystemVerilogBackend(all_pins=True, desc_comms=False, mod_stubs=True)
        [out] = list(backend.serialize(backend.represent(top), combine=True))

        verilog_path = tmp_path / f"{modname}.sv"
        verilog_path.write_text(out.content)

        modules2 = {m.id.name: m for m in frontend.parse_files([verilog_path]).modules}
        top2 = modules2[modname]
        [out2] = list(backend.serialize(backend.represent(top2), combine=True))

        assert normalize_sv(out.content) == normalize_sv(out2.content)
