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


class Interface:
    """ Helper class, representing a KPM node's interface
    """
    def __init__(self, node_name: str, iface_name: str, iface_id: str):
        self.node_name = node_name
        self.iface_name = iface_name
        self.iface_id = iface_id

    def __repr__(self) -> str:
        return self.node_name + ":" + self.iface_name

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Interface):
            return value.iface_id == self.iface_id
        return False


def _get_interface_connections(dataflow_data, iface: Interface) -> list:
    """ Return a list of connections from/to a given interface
    """
    return [
        conn for conn in dataflow_data['graph']['connections'] if conn['from'] == iface.iface_id or conn['to'] == iface.iface_id
    ]


def _get_ips_interfaces(dataflow_data) -> list:
    """ Return a list of all the interfaces of all the nodes representing ip cores
    """
    result = []
    for node in _get_ip_nodes(dataflow_data):
        for interface in node['interfaces']:
            result.append(Interface(node['name'], interface['name'], interface['id']))
    return result


def _get_ip_nodes(dataflow_data) -> list:
    """ Return a list of nodes which represent ip cores
    (i.e. filter out External Outputs and Inputs)
    """
    return [
        node for node in dataflow_data['graph']['nodes'] if node['type'] not in ['External Output', 'External Input']
    ]

def _get_externals_ifaces_ids(dataflow_data) -> list:
    """ Return a list of ids, which identify metainterfaces of external metanodes
    """
    ext_nodes_ifaces_ids = []
    for node in dataflow_data['graph']['nodes']:
        if node['type'] in ['External Input', 'External Output']:
            ext_nodes_ifaces_ids.append(node['interfaces'][0]['id'])
    return ext_nodes_ifaces_ids


def _check_duplicate_ip_names(dataflow_data, specification) -> CheckResult:
    """ Check for duplicate IP core names in the design.
    """
    names_set = set()
    duplicates = set()
    for node in _get_ip_nodes(dataflow_data):
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

    for node in _get_ip_nodes(dataflow_data):
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


def find_dataflow_interface_by_id(dataflow_json, iface_id: str) -> list | None:
    """ Return a list ["node_name", "iface_name"] that corresponds to
    a given 'iface_id'
    """
    ip_interfaces = get_dataflow_ips_interfaces(dataflow_json)

    if iface_id in ip_interfaces.keys():
        return ip_interfaces[iface_id]


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


def find_spec_interface_by_name(
        specification,
        node_type: str,
        iface_name: str):

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
    ext_nodes_ifaces_ids = _get_externals_ifaces_ids(dataflow_data)

    err_conns_ids = []
    for conn in dataflow_data['graph']['connections']:
        if conn['from'] in ext_nodes_ifaces_ids and conn['to'] in ext_nodes_ifaces_ids:
            err_conns_ids.append((conn['from'], conn['id']))

    if not err_conns_ids:
        return CheckResult(CheckStatus.OK, None)
    return CheckResult(CheckStatus.ERROR, f"Existing connections from External Inputs to External Outputs")


def _check_ambigous_ports_interfaces(dataflow_data, specification):
    """ Check for interfaces which are connected to another ipcore interface
    and to external metanode at the same time
    """
    ext_nodes_ifaces_ids = _get_externals_ifaces_ids(dataflow_data)

    ambig_ifaces = []
    for iface in _get_ips_interfaces(dataflow_data):
        iface_conns = _get_interface_connections(dataflow_data, iface)
        for conn in iface_conns:
            if (conn['from'] in ext_nodes_ifaces_ids or conn['to'] in ext_nodes_ifaces_ids) and len(iface_conns) > 1:
                ambig_ifaces.append(iface)
                break

    if not ambig_ifaces:
        return CheckResult(CheckStatus.OK, None)
    return CheckResult(CheckStatus.ERROR, f"External interfaces having >1 connections: {ambig_ifaces}")


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
