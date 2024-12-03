# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from pipeline_manager_backend_communication.misc_structures import MessageType
from pytest_lazy_fixtures import lf

from topwrap.kpm_dataflow_validator import DataflowValidator
from topwrap.util import JsonType, read_json_file


def get_dataflow_test(test_name: str) -> JsonType:
    return read_json_file(Path(f"tests/data/data_kpm/dataflow_tests/{test_name}.json"))


@pytest.fixture
def dataflow_duplicate_ip_names():
    """
    Dataflow containing two IP cores with the same instance name.
    This is considered as not possible to represent in design yaml since we can't distinguish them.
    """
    return get_dataflow_test("dataflow_duplicate_ips")


@pytest.fixture
def dataflow_invalid_parameters_values():
    """
    Dataflow containing an IP core with multiple parameters, but it's impossible to resolve the `INVALID NAME!!!`.
    """
    return get_dataflow_test("dataflow_invalid_params")


@pytest.fixture
def dataflow_ext_in_to_ext_out_connections():
    """Dataflow containing Metanode<->Metanode connection."""
    return get_dataflow_test("dataflow_meta_to_meta_conn")


@pytest.fixture
def dataflow_ports_multiple_external_metanodes():
    """Dataflow containing a port connected to two External Metanodes."""
    return get_dataflow_test("dataflow_port_to_multiple_external_metanodes")


@pytest.fixture
def dataflow_duplicate_metanode_names():
    """Dataflow containing two External Output Metanodes with the same "External Name" value."""
    return get_dataflow_test("dataflow_duplicate_metanode_names")


@pytest.fixture
def dataflow_duplicate_external_input_interfaces():
    """
    Dataflow containing two External Input Metanodes with the same name.
    Here connection is to interface instead of port as in the example above.
    """
    return get_dataflow_test("dataflow_duplicate_ext_input_ifaces")


@pytest.fixture
def dataflow_unnamed_metanodes():
    """Dataflow containing unnamed External Input Metanode with multiple connections to it."""
    return get_dataflow_test("dataflow_connected_unnamed_metanode")


@pytest.fixture
def dataflow_inouts_connections():
    """Dataflow containing a connection between two inout ports."""
    return get_dataflow_test("dataflow_inouts_connections")


@pytest.fixture
def dataflow_unconn_hierarchy():
    """Dataflow containing subgraph node with two unconnected interfaces."""
    return get_dataflow_test("dataflow_unconn_hierarchy")


@pytest.fixture
def dataflow_subgraph_multiple_external_metanodes():
    """Dataflow containing subgraph node with connection to two External Output Metanodes."""
    return get_dataflow_test("dataflow_subgraph_multiple_external_metanodes")


@pytest.fixture
def dataflow_conn_subgraph_metanode():
    """
    Dataflow containing subgraph metanode with connection to exposed interface.
    It can be seen by selecting the "Edit Subgraph" on subgraph node.
    """
    return get_dataflow_test("dataflow_conn_subgraph_metanode")


@pytest.fixture
def dataflow_complex_hierarchy():
    """Dataflow containing many edge cases such as duplicate subgraph node names, stressing out the capabilities of saving a design."""
    return get_dataflow_test("../conversions/complex/dataflow_complex")


@pytest.fixture
def dataflow_hier_duplicate_names():
    """Dataflow containing subgraph node inside which are duplicate IP's."""
    return get_dataflow_test("dataflow_hierarchical_duplicate_names")


# Test validation checks by running them on HDMI dataflow
@pytest.mark.parametrize(
    "check_function, expected_result",
    [
        (DataflowValidator.check_duplicate_node_names, MessageType.OK),
        (DataflowValidator.check_parameters_values, MessageType.OK),
        (DataflowValidator.check_external_in_to_external_out_connections, MessageType.OK),
        (DataflowValidator.check_port_to_multiple_external_metanodes, MessageType.OK),
        (DataflowValidator.check_unnamed_external_metanodes_with_multiple_conn, MessageType.OK),
        (DataflowValidator.check_duplicate_metanode_names, MessageType.OK),
        (DataflowValidator.check_connection_to_subgraph_metanodes, MessageType.OK),
        (DataflowValidator.check_unconnected_ports_interfaces, MessageType.WARNING),
        (DataflowValidator.check_inouts_connections, MessageType.OK),
    ],
)
def test_hdmi_dataflow_validation(check_function, expected_result, hdmi_dataflow):
    check_result = check_function(DataflowValidator(hdmi_dataflow))
    assert check_result.status == expected_result


# Test validation checks by running them on PWM dataflow
@pytest.mark.parametrize(
    "check_function, expected_result",
    [
        (DataflowValidator.check_duplicate_node_names, MessageType.OK),
        (DataflowValidator.check_parameters_values, MessageType.OK),
        (DataflowValidator.check_external_in_to_external_out_connections, MessageType.OK),
        (DataflowValidator.check_port_to_multiple_external_metanodes, MessageType.OK),
        (DataflowValidator.check_unnamed_external_metanodes_with_multiple_conn, MessageType.OK),
        (DataflowValidator.check_duplicate_metanode_names, MessageType.OK),
        (DataflowValidator.check_connection_to_subgraph_metanodes, MessageType.OK),
        (DataflowValidator.check_unconnected_ports_interfaces, MessageType.WARNING),
        (DataflowValidator.check_inouts_connections, MessageType.OK),
    ],
)
def test_pwm_dataflow_validation(check_function, expected_result, pwm_dataflow):
    check_result = check_function(DataflowValidator(pwm_dataflow))
    assert check_result.status == expected_result


# Test validation checks by running them on hierarchy dataflow
@pytest.mark.parametrize(
    "check_function, expected_result",
    [
        (DataflowValidator.check_duplicate_node_names, MessageType.OK),
        (DataflowValidator.check_parameters_values, MessageType.OK),
        (DataflowValidator.check_external_in_to_external_out_connections, MessageType.OK),
        (DataflowValidator.check_port_to_multiple_external_metanodes, MessageType.OK),
        (DataflowValidator.check_unnamed_external_metanodes_with_multiple_conn, MessageType.OK),
        (DataflowValidator.check_duplicate_metanode_names, MessageType.OK),
        (DataflowValidator.check_connection_to_subgraph_metanodes, MessageType.OK),
        (DataflowValidator.check_unconnected_ports_interfaces, MessageType.WARNING),
        (DataflowValidator.check_inouts_connections, MessageType.OK),
    ],
)
def test_hierarchy_dataflow_validation(check_function, expected_result, hierarchy_dataflow):
    check_result = check_function(DataflowValidator(hierarchy_dataflow))
    assert check_result.status == expected_result


@pytest.mark.parametrize(
    "check_function, expected_result",
    [
        (DataflowValidator.check_duplicate_node_names, MessageType.WARNING),
        (DataflowValidator.check_parameters_values, MessageType.OK),
        (DataflowValidator.check_external_in_to_external_out_connections, MessageType.OK),
        (DataflowValidator.check_port_to_multiple_external_metanodes, MessageType.OK),
        (DataflowValidator.check_unnamed_external_metanodes_with_multiple_conn, MessageType.OK),
        (DataflowValidator.check_duplicate_metanode_names, MessageType.OK),
        (DataflowValidator.check_connection_to_subgraph_metanodes, MessageType.OK),
        (DataflowValidator.check_unconnected_ports_interfaces, MessageType.WARNING),
        (DataflowValidator.check_inouts_connections, MessageType.OK),
    ],
)
def test_complex_hierarchy_dataflow_validation(
    check_function, expected_result, dataflow_complex_hierarchy
):
    check_result = check_function(DataflowValidator(dataflow_complex_hierarchy))
    assert check_result.status == expected_result


# Test validation checks on some simple erroneous dataflows
@pytest.mark.parametrize(
    "check_function, dataflow, expected_result",
    [
        (
            DataflowValidator.check_duplicate_node_names,
            lf("dataflow_duplicate_ip_names"),
            MessageType.WARNING,
        ),
        (
            DataflowValidator.check_parameters_values,
            lf("dataflow_invalid_parameters_values"),
            MessageType.WARNING,
        ),
        (
            DataflowValidator.check_external_in_to_external_out_connections,
            lf("dataflow_ext_in_to_ext_out_connections"),
            MessageType.ERROR,
        ),
        (
            DataflowValidator.check_port_to_multiple_external_metanodes,
            lf("dataflow_ports_multiple_external_metanodes"),
            MessageType.ERROR,
        ),
        (
            DataflowValidator.check_unnamed_external_metanodes_with_multiple_conn,
            lf("dataflow_unnamed_metanodes"),
            MessageType.ERROR,
        ),
        (
            DataflowValidator.check_duplicate_metanode_names,
            lf("dataflow_duplicate_metanode_names"),
            MessageType.ERROR,
        ),
        (
            DataflowValidator.check_unconnected_ports_interfaces,
            lf("dataflow_duplicate_external_input_interfaces"),
            MessageType.WARNING,
        ),
        (
            DataflowValidator.check_inouts_connections,
            lf("dataflow_inouts_connections"),
            MessageType.WARNING,
        ),
    ],
)
def test_invalid_dataflow_validation(dataflow, check_function, expected_result):
    check_result = check_function(DataflowValidator(dataflow))
    assert check_result.status == expected_result


# Test validation on some hierarchy cases
@pytest.mark.parametrize(
    "check_function, dataflow, expected_result, error_count",
    [
        (
            DataflowValidator.check_duplicate_node_names,
            lf("dataflow_hier_duplicate_names"),
            MessageType.WARNING,
            1,
        ),
        (
            DataflowValidator.check_unconnected_ports_interfaces,
            lf("dataflow_unconn_hierarchy"),
            MessageType.WARNING,
            2,
        ),
        (
            DataflowValidator.check_port_to_multiple_external_metanodes,
            lf("dataflow_subgraph_multiple_external_metanodes"),
            MessageType.ERROR,
            1,
        ),
        (
            DataflowValidator.check_connection_to_subgraph_metanodes,
            lf("dataflow_conn_subgraph_metanode"),
            MessageType.ERROR,
            1,
        ),
    ],
)
def test_invalid_hierarchy_dataflow_validation(
    dataflow,
    check_function,
    expected_result,
    error_count,
):
    check_result = check_function(DataflowValidator(dataflow))
    assert check_result.status == expected_result
    assert check_result.error_count == error_count
