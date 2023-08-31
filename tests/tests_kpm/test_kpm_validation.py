# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
from pytest_lazy_fixtures import lf

from fpga_topwrap.kpm_dataflow_validator import (
    CheckStatus,
    _check_ambigous_ports,
    _check_duplicate_external_input_interfaces,
    _check_duplicate_external_out_inout_names,
    _check_duplicate_ip_names,
    _check_ext_in_to_ext_out_connections,
    _check_external_inputs_missing_val,
    _check_parameters_values,
    _check_unconnected_ports_interfaces,
)
from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from tests.common import read_json_file


@pytest.fixture
def dataflow_duplicate_ip_names():
    """Dataflow containing 2 IP cores with the same name."""
    return read_json_file("tests/data/data_kpm/dataflow_duplicate_ips.json")


@pytest.fixture
def dataflow_invalid_parameters_values():
    """Dataflow containing an IP core with parameter in wrong format"""
    return read_json_file("tests/data/data_kpm/dataflow_invalid_params.json")


@pytest.fixture
def dataflow_ext_in_to_ext_out_connections():
    """Dataflow containing Metanode<->Metanode connection"""
    return read_json_file("tests/data/data_kpm/dataflow_meta_to_meta_conn.json")


@pytest.fixture
def dataflow_ambigous_ports():
    """Dataflow containing a port connected to another port and a metanode simultaneously"""
    return read_json_file("tests/data/data_kpm/dataflow_ambigous_ports.json")


@pytest.fixture
def dataflow_external_metanodes_types_mismatch():
    """Dataflow containing a connection from output port to External Inout"""
    return read_json_file("tests/data/data_kpm/dataflow_external_metanodes_mismatch.json")


@pytest.fixture
def dataflow_duplicate_ext_out_port_names():
    """Dataflow containing two External Output metanodes with the same "External Name" value"""
    return read_json_file("tests/data/data_kpm/dataflow_duplicate_ext_out_ports.json")


@pytest.fixture
def dataflow_missing_ext_input_value():
    """Dataflow containing External Input metanode connected to 2 nodes representing IP cores
    with missing "External Name" value
    """
    return read_json_file("tests/data/data_kpm/dataflow_missing_ext_input.json")


@pytest.fixture
def dataflow_duplicate_external_input_interfaces():
    """Dataflow containing two external input interfaces with the same name"""
    return read_json_file("tests/data/data_kpm/dataflow_duplicate_ext_input_ifaces.json")


@pytest.fixture
def specification_duplicate_external_input_interfaces():
    """Specification compatible with `dataflow_duplicate_external_input_interfaces`"""
    return read_json_file("tests/data/data_kpm/spec_duplicate_ext_input_ifaces.json")


# Test validation checks by running them on PWM dataflow
@pytest.mark.parametrize(
    "_check_function, expected_result",
    [
        (_check_duplicate_ip_names, CheckStatus.OK),
        (_check_parameters_values, CheckStatus.OK),
        (_check_ext_in_to_ext_out_connections, CheckStatus.OK),
        (_check_ambigous_ports, CheckStatus.OK),
        (_check_external_inputs_missing_val, CheckStatus.OK),
        (_check_duplicate_external_input_interfaces, CheckStatus.OK),
        (_check_duplicate_external_out_inout_names, CheckStatus.OK),
        (_check_unconnected_ports_interfaces, CheckStatus.WARNING),
    ],
)
def test_hdmi_dataflow_validation(
    _check_function, expected_result, hdmi_dataflow, hdmi_ipcores_yamls
):
    hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
    status, msg = _check_function(hdmi_dataflow, hdmi_specification)
    assert status == expected_result


# Test validation checks by running them on HDMI dataflow
@pytest.mark.parametrize(
    "_check_function, expected_result",
    [
        (_check_duplicate_ip_names, CheckStatus.OK),
        (_check_parameters_values, CheckStatus.OK),
        (_check_ext_in_to_ext_out_connections, CheckStatus.OK),
        (_check_ambigous_ports, CheckStatus.OK),
        (_check_external_inputs_missing_val, CheckStatus.OK),
        (_check_duplicate_external_input_interfaces, CheckStatus.OK),
        (_check_duplicate_external_out_inout_names, CheckStatus.OK),
        (_check_unconnected_ports_interfaces, CheckStatus.WARNING),
    ],
)
def test_pwm_dataflow_validation(_check_function, expected_result, pwm_dataflow, pwm_ipcores_yamls):
    pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
    status, msg = _check_function(pwm_dataflow, pwm_specification)
    assert status == expected_result


# Test validation checks on some simple erroneous dataflows
@pytest.mark.parametrize(
    "_check_function, dataflow, specification, expected_result",
    [
        (_check_duplicate_ip_names, lf("dataflow_duplicate_ip_names"), None, CheckStatus.ERROR),
        (
            _check_parameters_values,
            lf("dataflow_invalid_parameters_values"),
            None,
            CheckStatus.ERROR,
        ),
        (
            _check_ext_in_to_ext_out_connections,
            lf("dataflow_ext_in_to_ext_out_connections"),
            None,
            CheckStatus.ERROR,
        ),
        (_check_ambigous_ports, lf("dataflow_ambigous_ports"), None, CheckStatus.ERROR),
        (
            _check_duplicate_external_out_inout_names,
            lf("dataflow_duplicate_ext_out_port_names"),
            None,
            CheckStatus.ERROR,
        ),
        (
            _check_external_inputs_missing_val,
            lf("dataflow_missing_ext_input_value"),
            None,
            CheckStatus.WARNING,
        ),
        (
            _check_duplicate_external_input_interfaces,
            lf("dataflow_duplicate_external_input_interfaces"),
            lf("specification_duplicate_external_input_interfaces"),
            CheckStatus.ERROR,
        ),
    ],
)
def test_invalid_dataflow_validation(dataflow, specification, _check_function, expected_result):
    status, msg = _check_function(dataflow, specification)
    assert status == expected_result
