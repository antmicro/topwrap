# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
import jsonschema
from yaml import load, Loader

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from fpga_topwrap.kpm_topwrap_client import _ipcore_names_to_yamls_mapping


@pytest.fixture
def pwm_ipcores_yamls() -> list:
    return [
        'fpga_topwrap/ips/axi/axi_axil_adapter.yaml',
        'examples/pwm/ipcores/ps7.yaml',
        'examples/pwm/ipcores/litex_pwm.yml'
    ]


@pytest.fixture
def pwm_ipcores_names_to_yamls(pwm_ipcores_yamls) -> dict:
    return _ipcore_names_to_yamls_mapping(pwm_ipcores_yamls)


@pytest.fixture
def pwm_design_yaml() -> dict:
    with open('examples/pwm/project.yml', 'r') as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


def test_pwm_specification_generation(specification_schema, pwm_ipcores_yamls):
    spec = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
    assert len(spec['nodes']) == 5 # 3 IP cores + 2 External metanodes
    jsonschema.validate(spec, specification_schema)
