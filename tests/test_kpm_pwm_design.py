# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
import jsonschema
from yaml import load, Loader

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from fpga_topwrap.kpm_topwrap_client import _ipcore_names_to_yamls_mapping
from fpga_topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from fpga_topwrap.kpm_common import *


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


@pytest.fixture
def pwm_specification(pwm_ipcores_yamls) -> dict:
    return ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)


@pytest.fixture
def pwm_dataflow(pwm_design_yaml, pwm_specification) -> dict:
    return kpm_dataflow_from_design_descr(pwm_design_yaml, pwm_specification)


def test_pwm_specification_generation(pwm_specification, specification_schema):
    assert len(pwm_specification['nodes']) == 5 # 3 IP cores + 2 External metanodes
    jsonschema.validate(pwm_specification, specification_schema)


def test_pwm_dataflow_import(pwm_dataflow):
    # check number of imported nodes
    assert len(pwm_dataflow['graph']['nodes']) == 4

    # check number of imported externals
    num_dataflow_externals = len(get_dataflow_metanodes(pwm_dataflow))
    assert num_dataflow_externals == 1

    # check connections between ip cores
    num_dataflow_ip_conns = len(get_dataflow_ip_connections(pwm_dataflow))
    assert num_dataflow_ip_conns == 7

    # check overrode parameter value
    axi_node = [node for node in pwm_dataflow['graph']['nodes'] if node['name'] == 'axi_bridge'][0]
    axi_id_width_prop = [prop for prop in axi_node['properties'] if prop['name'] == 'AXI_ID_WIDTH'][0]
    assert int(axi_id_width_prop['value']) == 12
