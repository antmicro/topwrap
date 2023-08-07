# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import pytest


@pytest.fixture
def specification_schema_path() -> Path:
    specification_schema_path = "kenning-pipeline-manager/pipeline_manager/resources/schemas/unresolved_specification_schema.json"  # noqa: E501
    return Path(specification_schema_path)


@pytest.fixture
def specification_schema(specification_schema_path) -> dict:
    with open(specification_schema_path, "r") as f:
        specification_schema = json.load(f)
    return specification_schema
