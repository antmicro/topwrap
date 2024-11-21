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
    InterfaceDefinitionSignals,
    InterfaceSignalType,
    get_interface_by_name,
)


class TestInterfaceDefinition:
    @pytest.fixture
    def iface(self) -> InterfaceDefinition:
        return InterfaceDefinition(
            name="barInterface",
            port_prefix="bar",
            signals=InterfaceDefinitionSignals.from_flat(
                [
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
                ]
            ),
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

    def test_predefined(self):
        assert (
            len(InterfaceDefinition.get_builtins()) == 5
        ), "No predefined interfaces could be retrieved"

    def test_iface_retrieve_by_name(self):
        name = "AXI4Stream"
        assert get_interface_by_name(name) is not None

    def test_iface_retrieve_by_name_negative(self):
        name = "zxcvbnm"
        assert get_interface_by_name(name) is None
