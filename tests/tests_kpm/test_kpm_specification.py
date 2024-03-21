# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import importlib.resources
from pathlib import Path

import pytest
from common import HDMI_ALL_UNIQUE_NODES, PWM_ALL_UNIQUE_NODES, read_json_file
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


def get_schema_path(schema_name) -> Path:
    with importlib.resources.path("pipeline_manager.resources.schemas", schema_name) as fd:
        return str(fd)


@pytest.fixture
def specification_schema() -> dict:
    """The contents of the main specification schema that is used for validating specifications"""
    return read_json_file(get_schema_path("specification_schema.json"))


@pytest.fixture
def schemas_names() -> list:
    """Return a list of helper schemas necessary for specification validation.
    These are "included" by the main `speficication_schema.json`.
    """
    return ["unresolved_specification_schema", "metadata_schema"]


@pytest.fixture
def schemas_registry(schemas_names) -> Registry:
    return Registry().with_resources(
        [
            (
                schema_name,
                DRAFT202012.create_resource(read_json_file(get_schema_path(f"{schema_name}.json"))),
            )
            for schema_name in schemas_names
        ]
    )


def test_pwm_specification_generation(specification_schema, pwm_ipcores_yamls, schemas_registry):
    """Validate generated specification for PWM design."""
    pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
    assert len(pwm_specification["nodes"]) == PWM_ALL_UNIQUE_NODES

    Draft202012Validator(specification_schema, registry=schemas_registry).validate(
        pwm_specification
    )


def test_hdmi_specification_generation(specification_schema, hdmi_ipcores_yamls, schemas_registry):
    """Validate generated specification for HDMI design."""
    hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
    assert len(hdmi_specification["nodes"]) == HDMI_ALL_UNIQUE_NODES

    Draft202012Validator(specification_schema, registry=schemas_registry).validate(
        hdmi_specification
    )
