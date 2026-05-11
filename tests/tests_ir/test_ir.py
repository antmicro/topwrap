# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

import pytest

from examples.ir_examples.modules import axis_streamer, intf_top
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.model.connections import PortDirection


class TestQuerableView:
    def test_regular_index(self):
        clk = intf_top._ports[0]
        assert intf_top.ports[0] is clk
        assert intf_top.ports[1] is not clk
        with pytest.raises(IndexError):
            intf_top.ports[3]

    def test_negative_index(self):
        clk, rst, ext = intf_top._ports
        assert intf_top.ports[-1] is ext
        assert intf_top.ports[-2] is rst
        assert intf_top.ports[-3] is clk
        with pytest.raises(IndexError):
            intf_top.ports[-4]

    def test_find(self):
        _, rst, ext = intf_top._ports
        assert intf_top.ports.find_by_name("rst") is rst
        assert intf_top.ports.find_by(lambda p: p.direction is PortDirection.INOUT) is ext
        assert intf_top.ports.find_by_name("gugugaga") is None

    def test_combined(self):
        assert len(axis_streamer.ios) == len(axis_streamer.ports) + len(axis_streamer.interfaces)
        assert axis_streamer.ios[4] is axis_streamer._interfaces[0] is axis_streamer.ios[-1]
        assert axis_streamer.ios[2] is axis_streamer._ports[2] is axis_streamer.ios[-3]


class TestAddressMaps:
    def test_address_map(self):
        frontend = YamlFrontend()
        frontend_output = frontend.parse_files(
            [Path("tests/data/data_parse/address_maps/design_one_map.yaml")]
        )
        assert frontend_output.modules[0].design is not None
        frontend_output.modules[0].design.update_interconnects_from_memory_maps()
        interconnect = frontend_output.modules[0].design._interconnects[0]
        subordinates = list(interconnect.subordinates.values())
        assert subordinates[0].address.elaborate() == 0x0
        assert subordinates[0].size.elaborate() == 0xA000
        assert subordinates[1].address.elaborate() == 0x10000000
        assert subordinates[1].size.elaborate() == 0x1000
        assert subordinates[2].address.elaborate() == 0xF0000000
        assert subordinates[2].size.elaborate() == 0x1000
        assert subordinates[3].address.elaborate() == 0xA0000000
        assert subordinates[3].size.elaborate() == 0x2F
        assert subordinates[4].address.elaborate() == 0xA1000000
        assert subordinates[4].size.elaborate() == 0x10

    def test_invalid_missing_iface(self, caplog: pytest.LogCaptureFixture):
        frontend = YamlFrontend()
        with caplog.at_level(logging.WARNING):
            frontend_output = frontend.parse_files(
                [Path("tests/data/data_parse/address_maps/design_invalid_missing_iface.yaml")]
            )
        assert frontend_output.modules[0].design is not None
        frontend_output.modules[0].design.update_interconnects_from_memory_maps()
        interconnect = frontend_output.modules[0].design._interconnects[0]
        subordinates = list(interconnect.subordinates.values())
        assert len(subordinates) == 3
        assert subordinates[0].address.elaborate() == 0x0
        assert subordinates[0].size.elaborate() == 0xA000
        assert subordinates[1].address.elaborate() == 0x10000000
        assert subordinates[1].size.elaborate() == 0x1000
        assert subordinates[2].address.elaborate() == 0xF0000000
        assert subordinates[2].size.elaborate() == 0x1000
        assert (
            "Skipping subordinate 'complex_subordinate' in address map 'map1' because subordinate "
            "has more that one interface, it is needed to specify which one needs to be connected"
            in caplog.text
        )

    def test_invalid_invalid_map(self, caplog: pytest.LogCaptureFixture):
        frontend = YamlFrontend()
        with caplog.at_level(logging.WARNING):
            frontend_output = frontend.parse_files(
                [Path("tests/data/data_parse/address_maps/design_invalid_invalid_map.yaml")]
            )
        assert frontend_output.modules[0].design is not None
        frontend_output.modules[0].design.update_interconnects_from_memory_maps()
        assert len(frontend_output.modules[0].design._interconnects) == 1
        interconnect = frontend_output.modules[0].design._interconnects[0]
        assert len(interconnect.subordinates) == 0

        assert (
            "Skipping memory map in 'interconnect0' interconnect, because of: Memory map: "
            "'non_existiend_map' is not defined" in caplog.text
        )
