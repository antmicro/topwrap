# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from topwrap.backend.yaml.common.interface_schema import InterfaceDefinitionDescription
from topwrap.config import library_scope
from topwrap.frontend.yaml.interface import InterfaceDefinitionDescriptionFrontend
from topwrap.model.interface import InterfaceDefinition


@pytest.fixture
def interface_parameter_data():
    data = Path(__file__).parents[1] / "data" / "data_ir" / "interface_parameters"
    with library_scope({"interface_parameters": str(data)}, replace=True):
        yield data


@pytest.fixture
def parameterized_bus_definition(interface_parameter_data: Path) -> InterfaceDefinition:
    return InterfaceDefinitionDescriptionFrontend().parse(
        InterfaceDefinitionDescription.load(interface_parameter_data / "bus.yaml")
    )
