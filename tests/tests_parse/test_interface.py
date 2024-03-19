# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Any

import pytest

from topwrap.common_serdes import NestedDict
from topwrap.hdl_parsers_utils import PortDirection
from topwrap.interface import (
    IfacePortSpecification,
    InterfaceDefinition,
    InterfaceSignalType,
)


class TestInterfaceDefinition:
    @pytest.fixture
    def iface(self) -> InterfaceDefinition:
        return InterfaceDefinition(
            name="barInterface",
            port_prefix="bar",
            signals=[
                IfacePortSpecification(
                    name="foo",
                    regexp=re.compile("foo"),
                    direction=PortDirection.IN,
                    type=InterfaceSignalType.REQUIRED,
                ),
                IfacePortSpecification(
                    name="baz",
                    regexp=re.compile("baz"),
                    direction=PortDirection.OUT,
                    type=InterfaceSignalType.REQUIRED,
                ),
                IfacePortSpecification(
                    name="foobar",
                    regexp=re.compile("foobar"),
                    direction=PortDirection.IN,
                    type=InterfaceSignalType.OPTIONAL,
                ),
                IfacePortSpecification(
                    name="foobaz",
                    regexp=re.compile("foobaz"),
                    direction=PortDirection.OUT,
                    type=InterfaceSignalType.OPTIONAL,
                ),
            ],
        )

    @pytest.fixture
    def signals(self) -> NestedDict[str, Any]:
        return {
            "in": {
                "foo": ("foo_signal", 32, 0, 0, 0),
                "foobar": ("foobar_signal", 20, 0, 0, 0),
            },
            "out": {
                "baz": ("baz_signal", 16, 0, 0, 0),
                "foobaz": ("foobaz_signal", 11, 0, 0, 0),
            },
        }

    def test_interfaces_presence(self):
        from topwrap import parsers as p

        interfaces = p.parse_interface_definitions()
        # parser returns non-empty list
        assert len(interfaces) == 5

    def test_predefined(self):
        from topwrap import interface

        assert (
            len(interface.interface_definitions) == 5
        ), "No predefined interfaces could be retrieved"

    def test_iface_retrieve_by_name(self):
        from topwrap import interface

        name = "AXI4Stream"
        assert interface.get_interface_by_name(name) is not None

    def test_iface_retrieve_by_name_negative(self):
        from topwrap import interface

        name = "zxcvbnm"
        assert interface.get_interface_by_name(name) is None

    def test_iface_compliance_all_present(
        self, iface: InterfaceDefinition, signals: NestedDict[str, Any]
    ):
        from topwrap import interface

        # all signals present
        assert interface.check_interface_compliance(iface, signals)

    def test_iface_compliance_opt_missing(
        self, iface: InterfaceDefinition, signals: NestedDict[str, Any]
    ):
        from topwrap import interface

        del signals["in"]["foobar"]
        # optional signal missing
        assert interface.check_interface_compliance(iface, signals)

    def test_iface_compliance_req_missing(
        self, iface: InterfaceDefinition, signals: NestedDict[str, Any]
    ):
        from topwrap import interface

        del signals["in"]["foo"]
        # required signal missing
        assert interface.check_interface_compliance(iface, signals) is False

    def test_iface_compliance_extra_signal(
        self, iface: InterfaceDefinition, signals: NestedDict[str, Any]
    ):
        from topwrap import interface

        signals["in"]["extra"] = ("extra_signal", 33, 0, 0, 0)
        # extra signal added
        assert interface.check_interface_compliance(iface, signals) is False
