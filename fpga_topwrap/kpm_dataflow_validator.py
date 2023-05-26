# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
import re
import numexpr as ex
import json
from enum import Enum
from typing import NamedTuple, Union
from .kpm_common import get_dataflow_ip_nodes, get_dataflow_externals_interfaces, get_dataflow_ips_interfaces, find_dataflow_interface_by_id, find_dataflow_node_type_by_name, find_spec_interface_by_name


class CheckStatus(Enum):
    OK = 0
    WARNING = 1
    ERROR = 2


class CheckResult(NamedTuple):
    status: CheckStatus
    message: Union[str, None]


def _check_duplicate_ip_names(dataflow_data, specification) -> CheckResult:
    """ Check for duplicate IP core names in the design.
    """
    names_set = set()
    duplicates = set()
    for node in get_dataflow_ip_nodes(dataflow_data):
        if node['name'] in names_set:
            duplicates.add(node['name'])
        else:
            names_set.add(node['name'])

    if not duplicates:
        return CheckResult(CheckStatus.OK, None)

    err_msg = f"Duplicate block names: {str(list(duplicates))}"
    return CheckResult(CheckStatus.ERROR, err_msg)


def _check_parameters_values(dataflow_data, specification) -> CheckResult:
    invalid_params = list()

    for node in get_dataflow_ip_nodes(dataflow_data):
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


def _check_unconnected_interfaces(dataflow_data, specification) -> CheckResult:
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
            [node_name, iface_name] = find_dataflow_interface_by_id(
                dataflow_data, unconn_iface_id
            )
            unconn_ifaces_descrs.append(f"{node_name}:{iface_name}")
        return CheckResult(
            CheckStatus.WARNING,
            f"Unconnected interfaces: {unconn_ifaces_descrs}"
        )
    return CheckResult(CheckStatus.OK, None)


def _check_multiple_connections_from_interfaces(dataflow_data, specification):
    """ Check for multiple connections going from interfaces.
    A single interfacemay have can be connected with only
    one other interface.
    """
    invalid_ifaces = []

    for iface in get_dataflow_ips_interfaces(dataflow_data).items():
        node_type = find_dataflow_node_type_by_name(dataflow_data, iface[1][0])
        iface_type = find_spec_interface_by_name(
            specification, node_type, iface[1][1])['type']
        if iface_type == "port":
            continue
        iface_conns = [
            conn for conn in dataflow_data['graph']['connections']
            if conn['from'] == iface[0] or conn['to'] == iface[0]
        ]
        if len(iface_conns) > 1:
            invalid_ifaces.append(iface)

    if invalid_ifaces:
        invalid_ifaces_descrs = [
            f"{invalid_iface[1][0]}:{invalid_iface[1][1]}"
            for invalid_iface in invalid_ifaces
        ]
        return CheckResult(
            CheckStatus.ERROR,
            f"Interfaces have >1 outgoing connection: {invalid_ifaces_descrs}"
        )
    return CheckResult(CheckStatus.OK, None)


def _check_ext_in_to_ext_out_connections(dataflow_data, specification):
    """ Check for connections between metanodes 'External Input' and 'External Output' metanodes
    """
    ext_ifaces_ids = get_dataflow_externals_interfaces(dataflow_data).keys()

    for conn in dataflow_data['graph']['connections']:
        if conn['from'] in ext_ifaces_ids and conn['to'] in ext_ifaces_ids:
            return CheckResult(CheckStatus.ERROR, f"Existing connections from External Inputs to External Outputs")

    return CheckResult(CheckStatus.OK, None)


def _check_ambigous_ports_interfaces(dataflow_data, specification):
    """ Check for interfaces which are connected to another ipcore interface
    and to external metanode at the same time
    """
    ext_ifaces_ids = get_dataflow_externals_interfaces(dataflow_data).keys()

    ambig_ifaces = []
    for iface in get_dataflow_ips_interfaces(dataflow_data).items():
        iface_conns =  [
            conn for conn in dataflow_data['graph']['connections'] if conn['from'] == iface[0] or conn['to'] == iface[0]
        ]
        for conn in iface_conns:
            if (conn['from'] in ext_ifaces_ids or conn['to'] in ext_ifaces_ids) and len(iface_conns) > 1:
                ambig_ifaces.append(iface)
                break

    if ambig_ifaces:
        ambig_ifaces_descrs = [
            f"{ambig_iface[1][0]}:{ambig_iface[1][1]}" for ambig_iface in ambig_ifaces
        ]
        return CheckResult(CheckStatus.ERROR, f"External ports/interfaces having >1 connections: {ambig_ifaces_descrs}")
    return CheckResult(CheckStatus.OK, None)


def validate_kpm_design(data: bytes, specification) -> dict:
    """ Run some checks to validate user-created design in KPM.
    Return a dict of warning and error messages to be sent to the KPM.
    """
    checks = [
        _check_duplicate_ip_names,
        _check_parameters_values,
        _check_unconnected_interfaces,
        _check_multiple_connections_from_interfaces,
        _check_ext_in_to_ext_out_connections,
        _check_ambigous_ports_interfaces
    ]

    messages = {
        "errors": [],
        "warnings": []
    }
    for check in checks:
        status, msg = check(json.loads(data.decode()), specification)
        if status == CheckStatus.ERROR:
            messages["errors"].append("ERROR: " + msg)
        elif status == CheckStatus.WARNING:
            messages["warnings"].append("WARNING: " + msg)

    return messages
