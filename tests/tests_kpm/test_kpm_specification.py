# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import jsonschema.validators
import pytest
from importlib_resources import _common
from jsonschema import Draft201909Validator
from referencing import Registry
from referencing.jsonschema import DRAFT201909

from topwrap.util import read_json_file
from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

SPEC_METANODES = 5  # Unique metanodes: Input, Output, Inout, Constant, Subgraph
PWM_UNIQUE_IPCORE_NODES = 3  # Unique IP Cores from examples/pwm/project.yaml
PWM_ALL_UNIQUE_NODES = PWM_UNIQUE_IPCORE_NODES + SPEC_METANODES
HDMI_UNIQUE_IPCORE_NODES = 12  # Unique IP Cores from examples/hdmi/project.yaml
HDMI_ALL_UNIQUE_NODES = HDMI_UNIQUE_IPCORE_NODES + SPEC_METANODES
HIERARCHY_UNIQUE_IPCORE_NODES = 8
HIERARCHY_ALL_UNIQUE_NODES = HIERARCHY_UNIQUE_IPCORE_NODES + SPEC_METANODES


def get_schema_path(schema_name) -> Path:
    # Based on https://github.com/python/importlib_resources/blob/66ea2dc7eb12b1be2322b7ad002cefb12d364dff/importlib_resources/_legacy.py#L84
    with _common.as_file(_common.files("pipeline_manager.resources.schemas") / schema_name) as fd:
        return fd


@pytest.fixture
def specification_schema() -> dict:
    """The contents of the main specification schema that is used for validating specifications"""
    return read_json_file(get_schema_path("specification_schema.json"))


@pytest.fixture
def schemas_names() -> list:
    """Return a list of helper schemas necessary for specification validation.
    These are "included" by the main `speficication_schema.json`.
    """
    return ["unresolved_specification_schema", "metadata_schema", "graph_schema"]


@pytest.fixture
def schemas_registry(schemas_names) -> Registry:
    return Registry().with_resources(
        [
            (
                schema_name,
                DRAFT201909.create_resource(read_json_file(get_schema_path(f"{schema_name}.json"))),
            )
            for schema_name in schemas_names
        ]
    )


# Whenever the JSON schema expects an array, only the
# Python `list` type is allowed in the validated object.
# This typechecker redefinition makes the `tuple` type also
# a valid representation of a JSON array.
# This is required because KPM specification builder outputs
# tuples instead of lists for some fields (e.g. `nodes`)
Validator = jsonschema.validators.extend(
    Draft201909Validator,
    type_checker=Draft201909Validator.TYPE_CHECKER.redefine(
        "array", lambda _, inst: isinstance(inst, (list, tuple))
    ),
)


def test_pwm_specification_generation(specification_schema, pwm_design, schemas_registry):
    """Validate generated specification for PWM design."""
    pwm_specification = ipcore_yamls_to_kpm_spec([], pwm_design)
    assert len(pwm_specification["nodes"]) == PWM_ALL_UNIQUE_NODES

    Validator(specification_schema, registry=schemas_registry).validate(pwm_specification)


def test_hdmi_specification_generation(specification_schema, hdmi_design, schemas_registry):
    """Validate generated specification for HDMI design."""
    hdmi_specification = ipcore_yamls_to_kpm_spec([], hdmi_design)
    assert len(hdmi_specification["nodes"]) == HDMI_ALL_UNIQUE_NODES

    Validator(specification_schema, registry=schemas_registry).validate(hdmi_specification)


def test_hierarchy_specification_generation(
    specification_schema, hierarchy_design, schemas_registry
):
    """Validate generated specification for Hierarchy design."""
    hierarchy_spec = ipcore_yamls_to_kpm_spec([], hierarchy_design)
    assert len(hierarchy_spec["nodes"]) == HIERARCHY_ALL_UNIQUE_NODES

    Validator(specification_schema, registry=schemas_registry).validate(hierarchy_spec)
