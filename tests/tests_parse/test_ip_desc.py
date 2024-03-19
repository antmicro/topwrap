# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from typing import Any, Hashable

import pytest
import strictyaml
from deepdiff import DeepDiff

from topwrap.common_serdes import NestedDict
from topwrap.interface_grouper import standard_iface_grouper
from topwrap.ip_desc import IPCoreDescription
from topwrap.verilog_parser import VerilogModule


class TestIPCoreDescription:
    @pytest.fixture
    def ip_core_description(self, axi_verilog_module: VerilogModule) -> IPCoreDescription:
        return axi_verilog_module.to_ip_core_description(standard_iface_grouper())

    @pytest.fixture
    def expected_output(self, ip_core_description: IPCoreDescription) -> NestedDict[Hashable, Any]:
        with open("tests/data/data_parse/axi_axil_adapter.yaml") as f:
            return dict(strictyaml.load("\n".join(f.readlines()), ip_core_description.schema).data)

    def defaultdict_to_dict(self, d: defaultdict):
        if isinstance(d, defaultdict):
            d = {k: self.defaultdict_to_dict(v) for k, v in d.items()}
        return d

    def test_format_conversion(
        self, ip_core_description: IPCoreDescription, expected_output: NestedDict[Hashable, Any]
    ):
        assert DeepDiff(self.defaultdict_to_dict(ip_core_description.format()), expected_output)
