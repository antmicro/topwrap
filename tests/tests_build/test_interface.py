# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from pytest import raises


class TestInterfaceDef:
    def test_interfaces_presence(self):
        from topwrap import parsers as p

        interfaces = p.parse_interface_definitions()
        # parser returns non-empty list
        assert interfaces

    def test_predefined(self):
        from topwrap import interface

        assert interface.interface_definitions, "No predefined interfaces " "could be retrieved"

    def test_iface_retrieve_by_name(self):
        from topwrap import interface

        name = "AXI4Stream"
        assert interface.get_interface_by_name(name)

    def test_iface_retrieve_by_name_negative(self):
        from topwrap import interface

        name = "zxcvbnm"
        assert interface.get_interface_by_name(name) is None

    def test_iface_retrieve_by_prefix(self):
        from topwrap import interface

        prefix = "AXIS"
        assert interface.get_interface_by_prefix(prefix)

    def test_iface_retrieve_by_prefix_negative(self):
        from topwrap import interface

        prefix = "zxcvbnm"
        assert interface.get_interface_by_prefix(prefix) is None


class TestInterfaces:
    def test_iface_match(self):
        from topwrap import util

        ports_correct = (("port1", "AXIS_0_TVALID"), ("port2", "AXIS_0_TREADY"))
        # signal name does not belong to the interface
        ports_incorrect = (("port1", "AXIS_0_TVALID"), ("port2", "AXIS_0_000000"))
        # interface prefixes don't match
        ports_incorrect2 = (("port1", "AXIS_0_TVALID"), ("port2", "AXI_0_TREADY"))
        # interface instances don't match
        ports_incorrect3 = (("port1", "AXIS_0_TVALID"), ("port2", "AXIS_1_TREADY"))
        correct = util.match_interface(ports_correct)
        assert correct["name"] == "AXI4Stream"
        assert correct["ports"]
        with raises(ValueError):
            util.match_interface(ports_incorrect)
        with raises(ValueError):
            util.match_interface(ports_incorrect2)
        with raises(ValueError):
            util.match_interface(ports_incorrect3)
