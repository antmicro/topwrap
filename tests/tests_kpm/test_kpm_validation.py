# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from pipeline_manager_backend_communication.misc_structures import MessageType
from pytest_lazy_fixtures import lf

from topwrap.kpm_dataflow_validator import (
    _check_ambigous_ports,
    _check_duplicate_external_input_interfaces,
    _check_duplicate_external_out_names,
    _check_duplicate_ip_names,
    _check_ext_in_to_ext_out_connections,
    _check_external_inputs_missing_val,
    _check_inouts_connections,
    _check_parameters_values,
    _check_unconnected_ports_interfaces,
)
from topwrap.util import JsonType, read_json_file


def get_dataflow_test(test_name: str) -> JsonType:
    return read_json_file(Path(f"tests/data/data_kpm/dataflow_tests/{test_name}.json"))


@pytest.fixture
def dataflow_duplicate_ip_names():
    """Dataflow containing 2 IP cores with the same name."""
    return get_dataflow_test("dataflow_duplicate_ips")


@pytest.fixture
def dataflow_invalid_parameters_values():
    """Dataflow containing an IP core with parameter in wrong format"""
    return get_dataflow_test("dataflow_invalid_params")


@pytest.fixture
def dataflow_ext_in_to_ext_out_connections():
    """Dataflow containing Metanode<->Metanode connection"""
    return get_dataflow_test("dataflow_meta_to_meta_conn")


@pytest.fixture
def dataflow_ambigous_ports():
    """Dataflow containing a port connected to another port and a metanode simultaneously"""
    return get_dataflow_test("dataflow_ambigous_ports")


@pytest.fixture
def dataflow_external_metanodes_types_mismatch():
    """Dataflow containing a connection from output port to External Inout"""
    return get_dataflow_test("dataflow_external_metanodes_mismatch")


@pytest.fixture
def dataflow_duplicate_ext_out_port_names():
    """Dataflow containing two External Output metanodes with the same "External Name" value"""
    return get_dataflow_test("dataflow_duplicate_ext_out_ports")


@pytest.fixture
def dataflow_missing_ext_input_value():
    """Dataflow containing External Input metanode connected to 2 nodes representing IP cores
    with missing "External Name" value
    """
    return get_dataflow_test("dataflow_missing_ext_input")


@pytest.fixture
def dataflow_duplicate_external_input_interfaces():
    """Dataflow containing two external input interfaces with the same name"""
    return get_dataflow_test("dataflow_duplicate_ext_input_ifaces")


@pytest.fixture
def dataflow_inouts_connections():
    """Dataflow containing a connection between two inout ports"""
    return get_dataflow_test("dataflow_inouts_connections")


# Test validation checks by running them on PWM dataflow
@pytest.mark.parametrize(
    "_check_function, expected_result",
    [
        (_check_duplicate_ip_names, MessageType.OK),
        (_check_parameters_values, MessageType.OK),
        (_check_ext_in_to_ext_out_connections, MessageType.OK),
        (_check_ambigous_ports, MessageType.OK),
        (_check_external_inputs_missing_val, MessageType.OK),
        (_check_duplicate_external_input_interfaces, MessageType.OK),
        (_check_duplicate_external_out_names, MessageType.OK),
        (_check_unconnected_ports_interfaces, MessageType.WARNING),
        (_check_inouts_connections, MessageType.OK),
    ],
)
def test_hdmi_dataflow_validation(
    _check_function, expected_result, hdmi_dataflow, hdmi_ipcores_yamls, hdmi_specification
):
    status, msg = _check_function(hdmi_dataflow, hdmi_specification)
    assert status == expected_result


# Test validation checks by running them on HDMI dataflow
@pytest.mark.parametrize(
    "_check_function, expected_result",
    [
        (_check_duplicate_ip_names, MessageType.OK),
        (_check_parameters_values, MessageType.OK),
        (_check_ext_in_to_ext_out_connections, MessageType.OK),
        (_check_ambigous_ports, MessageType.OK),
        (_check_external_inputs_missing_val, MessageType.OK),
        (_check_duplicate_external_input_interfaces, MessageType.OK),
        (_check_duplicate_external_out_names, MessageType.OK),
        (_check_unconnected_ports_interfaces, MessageType.WARNING),
        (_check_inouts_connections, MessageType.OK),
    ],
)
def test_pwm_dataflow_validation(_check_function, expected_result, pwm_dataflow, pwm_specification):
    status, msg = _check_function(pwm_dataflow, pwm_specification)
    assert status == expected_result


# Test validation checks on some simple erroneous dataflows
@pytest.mark.parametrize(
    "_check_function, dataflow, expected_result",
    [
        (_check_duplicate_ip_names, lf("dataflow_duplicate_ip_names"), MessageType.ERROR),
        (
            _check_parameters_values,
            lf("dataflow_invalid_parameters_values"),
            MessageType.ERROR,
        ),
        (
            _check_ext_in_to_ext_out_connections,
            lf("dataflow_ext_in_to_ext_out_connections"),
            MessageType.ERROR,
        ),
        (_check_ambigous_ports, lf("dataflow_ambigous_ports"), MessageType.ERROR),
        (
            _check_duplicate_external_out_names,
            lf("dataflow_duplicate_ext_out_port_names"),
            MessageType.ERROR,
        ),
        (
            _check_external_inputs_missing_val,
            lf("dataflow_missing_ext_input_value"),
            MessageType.WARNING,
        ),
        (
            _check_duplicate_external_input_interfaces,
            lf("dataflow_duplicate_external_input_interfaces"),
            MessageType.ERROR,
        ),
        (_check_inouts_connections, lf("dataflow_inouts_connections"), MessageType.WARNING),
    ],
)
def test_invalid_dataflow_validation(dataflow, _check_function, expected_result, pwm_specification):
    status, msg = _check_function(dataflow, pwm_specification)
    assert status == expected_result
