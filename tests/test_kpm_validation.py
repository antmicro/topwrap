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
    _check_externals_metanodes_types,
    _check_parameters_values,
    _check_unconnected_ports_interfaces,
)
from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


@pytest.fixture
def dataflow_duplicate_ip_names():
    """Dataflow containing 2 IP cores with the same name."""
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "ps7",
                    "id": "d92d0945-44ba-496b-94a2-c04cd92f0486",
                    "position": {"x": -240, "y": 60},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [],
                    "properties": [],
                    "name": "ps7",
                },
                {
                    "type": "ps7",
                    "id": "13fc35a4-bba5-40a3-bd28-5e7435d31819",
                    "position": {"x": -240, "y": 330},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [],
                    "properties": [],
                    "name": "ps7",
                },
            ],
            "connections": [],
            "panning": {"x": 1045, "y": 188},
            "scaling": 0.9476349596290801,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_invalid_parameters_values():
    """Dataflow containing an IP core with parameter in wrong format"""
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "axi_axil_adapter",
                    "id": "23324971-5d66-4369-af4e-a06fad5e3c4c",
                    "position": {"x": -240, "y": 15},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [],
                    "properties": [
                        {
                            "name": "ADDR_WIDTH",
                            "id": "999a5de6-d627-4ac9-9be6-2680949aa385",
                            "value": "INVALID_NAME!!!",
                        }
                    ],
                    "name": "axi_axil_adapter",
                }
            ],
            "connections": [],
            "panning": {"x": 1045, "y": 188},
            "scaling": 0.9476349596290801,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_ext_in_to_ext_out_connections():
    """Dataflow containing Metanode<->Metanode connection"""
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "External Input",
                    "id": "ee9c48a9-2ea4-4235-aa54-cda695e39f01",
                    "position": {"x": -375, "y": -15},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "a68a47e6-4421-4311-8ed2-03d3215cb241",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "f70c9fd5-a91f-40af-969f-d5af360e0e01",
                            "value": "",
                        }
                    ],
                    "name": "External Input",
                },
                {
                    "type": "External Inout",
                    "id": "d0ab7906-4ab5-46e9-a35b-221ea214e926",
                    "position": {"x": 30, "y": -15},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "f32ec2dc-62c8-499a-8a17-8c679c3c2466",
                            "direction": "inout",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "690b6bba-aa02-4175-a61c-fd1a99e3ff30",
                            "value": "",
                        }
                    ],
                    "name": "External Inout",
                },
            ],
            "connections": [
                {
                    "id": "5086cdfd-4cc9-4c2f-a0f5-85b0685a1adc",
                    "from": "a68a47e6-4421-4311-8ed2-03d3215cb241",
                    "to": "f32ec2dc-62c8-499a-8a17-8c679c3c2466",
                }
            ],
            "panning": {"x": 1003.9251414897619, "y": 150.35555743714838},
            "scaling": 0.9987521399140239,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_ambigous_ports():
    """Dataflow containing a port connected to another port and a metanode simultaneously"""
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "ps7",
                    "id": "232fe0ee-85ba-4708-9f37-4e490af79a4a",
                    "position": {"x": 75, "y": 90},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "FCLK0",
                            "id": "b2eb6d56-3dd3-4e08-8d78-54b03227bf72",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [],
                    "name": "ps7",
                },
                {
                    "type": "External Output",
                    "id": "a801ab6a-04c6-4b13-a3e3-58ba1836f184",
                    "position": {"x": 525, "y": 15},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "b4178d39-7280-49b9-b2fb-ffda592b18dc",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "62474956-6b2c-4598-a80e-6648b674a5ac",
                            "value": "",
                        }
                    ],
                    "name": "External Output",
                },
            ],
            "connections": [
                {
                    "id": "0d7b48e2-9fe8-4145-ac1c-fcc4f1e21404",
                    "from": "b2eb6d56-3dd3-4e08-8d78-54b03227bf72",
                    "to": "4fcfc8f0-d4ee-4a7f-be0c-9e215677244d",
                },
                {
                    "id": "4e6bd2f1-aa40-4dc2-b296-61ee809a54ef",
                    "from": "b2eb6d56-3dd3-4e08-8d78-54b03227bf72",
                    "to": "b4178d39-7280-49b9-b2fb-ffda592b18dc",
                },
            ],
            "panning": {"x": 791, "y": 290},
            "scaling": 0.9987521399140239,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_external_metanodes_types_mismatch():
    """Dataflow containing a connection from output port to External Inout"""
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "litex_pwm",
                    "id": "e8c958ea-676b-4a24-b3eb-417af629e251",
                    "position": {"x": -345, "y": 45},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "pwm",
                            "id": "7dd4df7b-13a6-4bae-8e66-e9cdf9ef0461",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [],
                    "name": "litex_pwm",
                },
                {
                    "type": "External Inout",
                    "id": "0f3c0e76-0c70-4b27-ac6a-ee346080ec2f",
                    "position": {"x": 75, "y": -30},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "8b72cc2d-d770-43c7-84cb-a54dd90e14dd",
                            "direction": "inout",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "8fd7960e-def7-49dc-b397-16ee41f7b77d",
                            "value": "",
                        }
                    ],
                    "name": "External Inout",
                },
            ],
            "connections": [
                {
                    "id": "76df4294-bbb2-4caf-b4d5-a5050500a395",
                    "from": "7dd4df7b-13a6-4bae-8e66-e9cdf9ef0461",
                    "to": "8b72cc2d-d770-43c7-84cb-a54dd90e14dd",
                }
            ],
            "panning": {"x": 791, "y": 290},
            "scaling": 0.9987521399140239,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_duplicate_ext_out_port_names():
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "litex_pwm",
                    "id": "e8c958ea-676b-4a24-b3eb-417af629e251",
                    "position": {"x": -270, "y": -45},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "pwm",
                            "id": "7dd4df7b-13a6-4bae-8e66-e9cdf9ef0461",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [],
                    "name": "litex_pwm",
                },
                {
                    "type": "litex_pwm",
                    "id": "97095923-1241-493b-abde-353528fe51a8",
                    "position": {"x": -270, "y": 180},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "pwm",
                            "id": "04592a3a-569a-4889-a26c-7f624599835c",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [],
                    "name": "litex_pwm",
                },
                {
                    "type": "External Output",
                    "id": "2be8fcdc-7b5c-47d0-a00f-353ea4fcaf73",
                    "position": {"x": 255, "y": -30},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "8835ee6b-8258-4f37-a9e4-075f1eaaf021",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "8ac0edc8-a209-4d96-af38-d38c943a4332",
                            "value": "ext_pwm",
                        }
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "268b0d63-813d-4215-ac24-b5aa11c533e9",
                    "position": {"x": 255, "y": 195},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "6c07c4ac-9fb9-411f-b03e-7883a5381874",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "ee6aa0d7-fbaa-4d55-9df9-a5a8fdf05abb",
                            "value": "ext_pwm",
                        }
                    ],
                    "name": "External Output",
                },
            ],
            "connections": [
                {
                    "id": "afb7a6c9-bfe3-4c1f-b33a-7d8e2a0cf0e2",
                    "from": "7dd4df7b-13a6-4bae-8e66-e9cdf9ef0461",
                    "to": "8835ee6b-8258-4f37-a9e4-075f1eaaf021",
                },
                {
                    "id": "61f5d86e-177b-41f5-92e6-ba8b9d45d688",
                    "from": "04592a3a-569a-4889-a26c-7f624599835c",
                    "to": "6c07c4ac-9fb9-411f-b03e-7883a5381874",
                },
            ],
            "panning": {"x": 791, "y": 290},
            "scaling": 0.9987521399140239,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_missing_ext_input_value():
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "ps7",
                    "id": "cb4100f5-cf42-413f-b499-fab73d136f7f",
                    "position": {"x": -15, "y": 15},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "MAXIGP0ACLK",
                            "id": "fd6b3645-f6c8-4c47-abb5-4d089fc4cd96",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [],
                    "name": "ps7",
                },
                {
                    "type": "External Input",
                    "id": "ee9edc66-6e5b-4e73-979f-e0b19193dcad",
                    "position": {"x": -975, "y": 195},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "fb5e64ae-a302-4ca3-91fd-3891563d848f",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "f786c887-2a62-4ada-a497-de1874032fb5",
                            "value": "",
                        }
                    ],
                    "name": "External Input",
                },
                {
                    "type": "ps7",
                    "id": "da4c87de-59f9-4c17-ad77-1fb7ed9dca93",
                    "position": {"x": -390, "y": 405},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "MAXIGP0ACLK",
                            "id": "2c01002f-d334-4005-b353-491291e6f42a",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [],
                    "name": "ps7_2",
                },
            ],
            "connections": [
                {
                    "id": "e00e2d1d-b522-4909-ac01-5f1e2b59d5fd",
                    "from": "fb5e64ae-a302-4ca3-91fd-3891563d848f",
                    "to": "fd6b3645-f6c8-4c47-abb5-4d089fc4cd96",
                },
                {
                    "id": "84c35418-ea66-4c5a-9797-960c8660593f",
                    "from": "fb5e64ae-a302-4ca3-91fd-3891563d848f",
                    "to": "2c01002f-d334-4005-b353-491291e6f42a",
                },
            ],
            "panning": {"x": 1361, "y": -55},
            "scaling": 0.9987521399140239,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def dataflow_duplicate_external_input_interfaces():
    return {
        "graph": {
            "id": "169115721638333",
            "nodes": [
                {
                    "type": "axi_axil_adapter",
                    "id": "d265fcbb-f9f1-453f-8754-1e8b688823ee",
                    "position": {"x": -300, "y": -330},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "s_axi",
                            "id": "5d9c9245-c892-4dcf-b07f-4cfa35e90916",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [],
                    "name": "axi_axil_adapter_1",
                },
                {
                    "type": "axi_axil_adapter",
                    "id": "74f51fda-666d-416b-91bc-d3839446fb26",
                    "position": {"x": -300, "y": 300},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "s_axi",
                            "id": "e2330e0b-d759-4ee3-8ec4-a26da8a63f32",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [],
                    "name": "axi_axil_adapter_2",
                },
                {
                    "type": "External Input",
                    "id": "16086ece-757e-4666-973e-6c9234f3f35e",
                    "position": {"x": -660, "y": 90},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "1a7e22a1-7e29-4c38-9f91-8d3caec0c41e",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "895fbf48-5c1b-48c0-9cea-93e99f59424a",
                            "value": "",
                        }
                    ],
                    "name": "External Input",
                },
                {
                    "type": "External Input",
                    "id": "2ddc2619-8893-438b-9a56-3a3c332ad6e8",
                    "position": {"x": -645, "y": 705},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "9d30971f-d9c9-447d-9950-7239ee407a6c",
                            "direction": "output",
                            "side": "right",
                        }
                    ],
                    "properties": [
                        {
                            "name": "External Name",
                            "id": "932df291-aff5-4d36-9ddd-bc42326189d1",
                            "value": "",
                        }
                    ],
                    "name": "External Input",
                },
            ],
            "connections": [
                {
                    "id": "37c397c0-f304-44f3-9973-ed57f7f8880b",
                    "from": "1a7e22a1-7e29-4c38-9f91-8d3caec0c41e",
                    "to": "5d9c9245-c892-4dcf-b07f-4cfa35e90916",
                },
                {
                    "id": "08bd3461-91f6-4210-974b-d07f222db1fe",
                    "from": "9d30971f-d9c9-447d-9950-7239ee407a6c",
                    "to": "e2330e0b-d759-4ee3-8ec4-a26da8a63f32",
                },
            ],
            "panning": {"x": 1980, "y": 477},
            "scaling": 0.6836922975942521,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def specification_duplicate_external_input_interfaces():
    return {
        "metadata": {
            "allowLoopbacks": True,
            "connectionStyle": "orthogonal",
            "movementStep": 15,
            "backgroundSize": 15,
        },
        "nodes": [
            {
                "name": "External Input",
                "type": "External Input",
                "category": "Metanode",
                "properties": [{"name": "External Name", "type": "text", "default": ""}],
                "interfaces": [{"name": "external", "type": "", "direction": "output"}],
            },
            {
                "name": "axi_axil_adapter",
                "type": "axi_axil_adapter",
                "category": "IPcore",
                "properties": [],
                "interfaces": [
                    {
                        "name": "s_axi",
                        "type": "iface_AXI4",
                        "direction": "input",
                        "maxConnectionsCount": 1,
                    }
                ],
            },
        ],
    }


# Test validation checks by running them on PWM dataflow
@pytest.mark.parametrize(
    "_check_function, expected_result",
    [
        (_check_duplicate_ip_names, CheckStatus.OK),
        (_check_parameters_values, CheckStatus.OK),
        (_check_ext_in_to_ext_out_connections, CheckStatus.OK),
        (_check_ambigous_ports, CheckStatus.OK),
        (_check_externals_metanodes_types, CheckStatus.OK),
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
        (_check_externals_metanodes_types, CheckStatus.OK),
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
            _check_externals_metanodes_types,
            lf("dataflow_external_metanodes_types_mismatch"),
            None,
            CheckStatus.ERROR,
        ),
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
