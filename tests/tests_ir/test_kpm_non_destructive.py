# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import pytest

from examples.ir_examples.interconnect.ir.wishbone import wishbone
from examples.ir_examples.interface.ir.axistream import axi_stream
from examples.ir_examples.modules import (
    hier_top,
    intf_top,
    intr_top,
    inv_top,
    simp_top,
)
from tests.tests_ir.kpm_helpers import _compare_modules
from topwrap.backend.kpm.backend import KpmBackend
from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.model.module import Module


class TestKpmNonDestructivity:
    @pytest.mark.parametrize("orig_module", [simp_top, intf_top, intr_top, hier_top, inv_top])
    def test_kpm_non_destructivity(
        self,
        orig_module: Module,
    ):
        backend = KpmBackend(depth=-1)
        repr = backend.represent(orig_module)
        [spec_info, flow_info] = backend.serialize(repr)

        frontend = KpmFrontend(interfaces=[wishbone, axi_stream])
        new_module = frontend.parse_str([spec_info.content, flow_info.content]).modules[-1]

        _compare_modules(orig_module, new_module)
