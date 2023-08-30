# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from referencing import Registry
from jsonschema import Draft202012Validator
from referencing.jsonschema import DRAFT202012

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from tests.common import read_json_file


@pytest.fixture()
def schemas_dir() -> Path:
    return Path("kenning-pipeline-manager/pipeline_manager/resources/schemas/")


@pytest.fixture
def specification_schema_path(schemas_dir) -> Path:
    return schemas_dir / Path("specification_schema.json")


@pytest.fixture
def specification_schema(specification_schema_path) -> dict:
    """The contents of the main specification schema that is used for validating specifications"""
    return read_json_file(specification_schema_path)


@pytest.fixture
def schemas_names() -> list:
    """Return a list of helper schemas necessary for specification validation.
    These are "included" by the main `speficication_schema.json`.
    """
    return ['unresolved_specification_schema', 'metadata_schema']


@pytest.fixture
def schemas_registry(schemas_dir, schemas_names) -> Registry:
    return Registry().with_resources([
        (schema_name, DRAFT202012.create_resource(
            read_json_file(schemas_dir / Path(f"{schema_name}.json"))))
        for schema_name in schemas_names
    ])


def test_pwm_specification_generation(specification_schema, pwm_ipcores_yamls, schemas_registry):
    """Validate generated specification for PWM design."""
    pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
    assert len(pwm_specification["nodes"]) == 6  # 3 IP cores + 3 External metanodes

    Draft202012Validator(specification_schema,
                         registry=schemas_registry).validate(pwm_specification)


def test_hdmi_specification_generation(specification_schema, hdmi_ipcores_yamls, schemas_registry):
    """Validate generated specification for HDMI design."""
    hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
    assert len(hdmi_specification["nodes"]) == 15  # 12 IP cores + 3 External metanodes

    Draft202012Validator(specification_schema,
                         registry=schemas_registry).validate(hdmi_specification)
