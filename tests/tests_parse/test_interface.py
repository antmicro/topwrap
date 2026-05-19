# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Any

import pytest

from topwrap.backend.yaml.common.interface_schema import (
    IfacePortSpecificationDescription,
    InterfaceDefinitionDescription,
    InterfaceDefinitionSignalsDescription,
    InterfaceSignalTypeDescription,
)
from topwrap.common_serdes import NestedDict
from topwrap.model.connections import PortDirection
from topwrap.model.misc import Identifier
from topwrap.repo.user_repo import InterfaceDefinitionResource
from topwrap.util import get_config


class TestInterfaceDefinition:
    @pytest.fixture
    def iface(self) -> InterfaceDefinitionDescription:
        return InterfaceDefinitionDescription(
            id=Identifier(name="barInterface"),
            signals=InterfaceDefinitionSignalsDescription.from_flat(
                [
                    IfacePortSpecificationDescription(
                        name="foo",
                        regexp=re.compile("foo"),
                        direction=PortDirection.IN,
                        type=InterfaceSignalTypeDescription.REQUIRED,
                    ),
                    IfacePortSpecificationDescription(
                        name="baz",
                        regexp=re.compile("baz"),
                        direction=PortDirection.OUT,
                        type=InterfaceSignalTypeDescription.REQUIRED,
                    ),
                    IfacePortSpecificationDescription(
                        name="foobar",
                        regexp=re.compile("foobar"),
                        direction=PortDirection.IN,
                        type=InterfaceSignalTypeDescription.OPTIONAL,
                    ),
                    IfacePortSpecificationDescription(
                        name="foobaz",
                        regexp=re.compile("foobaz"),
                        direction=PortDirection.OUT,
                        type=InterfaceSignalTypeDescription.OPTIONAL,
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
        assert len(get_config().builtin_repo.get_resources(InterfaceDefinitionResource)) == 5, (
            "No predefined interfaces could be retrieved"
        )
