# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import pytest

from examples.ir_examples.modules import axis_streamer, intf_top
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
