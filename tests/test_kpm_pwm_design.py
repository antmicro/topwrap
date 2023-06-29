# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
import jsonschema
import os

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


@pytest.fixture
def pwm_design_yamls() -> list:
    return [
        'fpga_topwrap/ips/axi/axi_axil_adapter.yaml',
        'examples/pwm/ipcores/ps7.yaml',
        'examples/pwm/ipcores/litex_pwm.yml'
    ]


def test_pwm_specification_generation(specification_schema, pwm_design_yamls):
    spec = ipcore_yamls_to_kpm_spec(pwm_design_yamls)
    assert len(spec['nodes']) == 5 # 3 IP cores + 2 External metanodes
    jsonschema.validate(spec, specification_schema)
