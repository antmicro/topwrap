# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
import re
import numexpr as ex
import json
from enum import Enum
from typing import NamedTuple, Union


class CheckStatus(Enum):
    OK = 0
    WARNING = 1
    ERROR = 2


class CheckResult(NamedTuple):
    status: CheckStatus
    message: Union[str, None]


def _check_duplicate_ip_names(data: bytes, specification) -> CheckResult:
    """ Check for duplicate IP core names in the design.
    """
    dataflow_data = json.loads(data.decode())
    names_set = set()
    duplicates = set()
    for node in dataflow_data['graph']['nodes']:
        if node['name'] in names_set:
            duplicates.add(node['name'])
        else:
            names_set.add(node['name'])

    if not duplicates:
        return CheckResult(CheckStatus.OK, None)

    err_msg = f"Duplicate block names: {str(list(duplicates))}"
    return CheckResult(CheckStatus.ERROR, err_msg)


def _check_parameters_values(data: bytes, specification) -> CheckResult:
    dataflow_data = json.loads(data.decode())
    invalid_params = list()

    for node in dataflow_data['graph']['nodes']:
        evaluated = dict()
        for property in node['properties']:
            param_name = property["name"]
            param_val = property["value"]
            if not re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
                try:
                    evaluated[param_name] = int(
                        ex.evaluate(param_val, evaluated).take(0))
                except (ValueError, KeyError, SyntaxError, OverflowError):
                    invalid_params.append(f"{node['name']}:{param_name}")

    if invalid_params:
        err_msg = f"Invalid parameters values: {str(invalid_params)}"
        return CheckResult(CheckStatus.ERROR, err_msg)
    return CheckResult(CheckStatus.OK, None)


def get_dataflow_ips_interfaces(dataflow_json) -> dict:
    result = {}
    for node in dataflow_json['graph']['nodes']:
        for interface in node['interfaces']:
            result[interface['id']] = [node['name'], interface['name']]
    return result


def find_dataflow_interface_by_id(dataflow_json, iface_id: str) -> list|None:
    """ Return a list ["node_name", "iface_name"] that corresponds to
    a given 'iface_id'
    """
    ip_interfaces = get_dataflow_ips_interfaces(dataflow_json)

    if iface_id in ip_interfaces.keys():
        return ip_interfaces[iface_id]


def _check_unconnected_interfaces(data: bytes, specification) -> CheckResult:
    dataflow_data = json.loads(data.decode())
    
    unconn_ifaces = set([
        interface['id']
        for node in dataflow_data['graph']['nodes'] 
        for interface in node['interfaces']
    ])

    for conn in dataflow_data['graph']['connections']:
        unconn_ifaces.discard(conn['from'])
        unconn_ifaces.discard(conn['to'])

    if unconn_ifaces:
        unconn_ifaces_descrs = []
        for unconn_iface_id in unconn_ifaces:
            [node_name, iface_name] = find_dataflow_interface_by_id(dataflow_data, unconn_iface_id)
            unconn_ifaces_descrs.append(f"{node_name}:{iface_name}")
        return CheckResult(CheckStatus.WARNING, f"Unconnected interfaces: {unconn_ifaces_descrs}")
    return CheckResult(CheckStatus.OK, None)


def find_spec_interface_by_name(specification, node_type: str, iface_name: str):
    for node in specification['nodes']:
        if node['type'] != node_type:
            continue
        for interface in node['interfaces']:
            if interface['name'] == iface_name:
                return interface


def find_dataflow_node_type_by_name(dataflow_data, node_name: str) -> str:
    for node in dataflow_data['graph']['nodes']:
        if node['name'] == node_name:
            return node["type"]


def _check_multiple_connections_from_interfaces(data: bytes, specification):
    """ Check for multiple connections going from interfaces. A single interface
    may have can be connected with only one other interface.
    """
    dataflow_data = json.loads(data.decode())
    invalid_ifaces = []
    
    for iface in get_dataflow_ips_interfaces(dataflow_data).items():
        node_type = find_dataflow_node_type_by_name(dataflow_data, iface[1][0])
        iface_type = find_spec_interface_by_name(specification, node_type, iface[1][1])['type']
        if iface_type == "port":
            continue
        iface_conns = [
            conn for conn in dataflow_data['graph']['connections'] if conn['from'] == iface[0] or conn['to'] == iface[0]
        ]
        if len(iface_conns) > 1:
            invalid_ifaces.append(iface)

    if invalid_ifaces:
        invalid_ifaces_descrs = [
            f"{invalid_iface[1][0]}:{invalid_iface[1][1]}" for invalid_iface in invalid_ifaces
        ]
        return CheckResult(CheckStatus.ERROR, f"Interfaces have >1 outgoing connection: {invalid_ifaces_descrs}")
    return CheckResult(CheckStatus.OK, None)


def validate_kpm_design(data: bytes, specification) -> dict:
    """ Run some checks to validate user-created design in KPM.
    Return a dict of warning and error messages to be sent to the KPM.
    """
    checks = [
        _check_duplicate_ip_names,
        _check_parameters_values,
        _check_unconnected_interfaces,
        _check_multiple_connections_from_interfaces
    ]

    messages = {
        "errors": [],
        "warnings": []
    }
    for check in checks:
        status, msg = check(data, specification)
        if status == CheckStatus.ERROR:
            messages["errors"].append("ERROR: " + msg)
        elif status == CheckStatus.WARNING:
            messages["warnings"].append("WARNING: " + msg)

    return messages
