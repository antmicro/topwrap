# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
import re
import numexpr as ex
import json
from enum import Enum
from typing import NamedTuple, Union
from .kpm_common import (
    EXT_OUTPUT_NAME,
    EXT_INPUT_NAME,
    EXT_INOUT_NAME,
    get_dataflow_ip_nodes,
    get_dataflow_externals_interfaces,
    get_dataflow_external_connections,
    get_dataflow_ips_interfaces,
    find_dataflow_interface_by_id
)


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


def _check_unconnected_ports_interfaces(
        dataflow_data,
        specification) -> CheckResult:

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
            interface = find_dataflow_interface_by_id(
                dataflow_data, unconn_iface_id
            )
            unconn_ifaces_descrs.append(
                f"{interface['node_name']}:{interface['iface_name']}"
            )
        return CheckResult(
            CheckStatus.WARNING,
            f"Unconnected interfaces: {unconn_ifaces_descrs}"
        )
    return CheckResult(CheckStatus.OK, None)


def _check_ext_in_to_ext_out_connections(dataflow_data, specification):
    """ Check for connections between external metanodes
    """
    ext_ifaces_ids = get_dataflow_externals_interfaces(dataflow_data).keys()

    for conn in dataflow_data['graph']['connections']:
        if conn['from'] in ext_ifaces_ids and conn['to'] in ext_ifaces_ids:
            return CheckResult(
                CheckStatus.ERROR,
                "Existing connections between external metanodes"
            )

    return CheckResult(CheckStatus.OK, None)


def _check_ambigous_ports(dataflow_data, specification):
    """ Check for ports which are connected to another ipcore port
    and to external metanode at the same time
    """
    ext_ifaces_ids = get_dataflow_externals_interfaces(dataflow_data).keys()

    ambig_ifaces = []
    for iface_id, iface in get_dataflow_ips_interfaces(dataflow_data).items():
        iface_conns = [
            conn for conn in dataflow_data['graph']['connections']
            if conn['from'] == iface_id or conn['to'] == iface_id
        ]
        for conn in iface_conns:
            if ((conn['from'] in ext_ifaces_ids
                    or conn['to'] in ext_ifaces_ids) and len(iface_conns)) > 1:
                ambig_ifaces.append(iface)
                break

    if ambig_ifaces:
        ambig_ifaces_descrs = [
            f"{ambig_iface['node_name']}:{ambig_iface['iface_name']}"
            for ambig_iface in ambig_ifaces
        ]
        return CheckResult(
            CheckStatus.ERROR,
            f"External ports having >1 connections: {ambig_ifaces_descrs}"
        )
    return CheckResult(CheckStatus.OK, None)


def _check_externals_metanodes_types(dataflow_data, specification):
    """ Check for external ports/interfaces which are connected to wrong type
    of external metanode. External outputs must be connected to
    `External Output` metanodes, external inputs to `External Input` etc.
    """
    bad_exts = []

    for conn in get_dataflow_external_connections(dataflow_data):
        iface_from = find_dataflow_interface_by_id(
            dataflow_data, conn['from'])
        iface_to = find_dataflow_interface_by_id(dataflow_data, conn['to'])
        if (iface_from["iface_dir"] == "inout"
                and iface_to["node_name"] == EXT_OUTPUT_NAME):
            bad_exts.append(
                f"{iface_from['node_name']}:{iface_from['iface_name']}")
        elif (iface_to["iface_dir"] == "inout"
              and iface_from["node_name"] == EXT_INPUT_NAME):
            bad_exts.append(
                f"{iface_to['node_name']}:{iface_to['iface_name']}")
        elif (iface_from["iface_dir"] == "output"
              and iface_to["node_name"] == EXT_INOUT_NAME):
            bad_exts.append(
                f"{iface_from['node_name']}:{iface_from['iface_name']}")
        elif (iface_to["iface_dir"] == "input"
              and iface_from["node_name"] == EXT_INOUT_NAME):
            bad_exts.append(
                f"{iface_to['node_name']}:{iface_to['iface_name']}")

    if bad_exts:
        return CheckResult(
            CheckStatus.ERROR,
            "External port/interfaces"
            f"connected to wrong type of external metanode: {bad_exts}"
        )
    return CheckResult(CheckStatus.OK, None)


def validate_kpm_design(data: bytes, specification) -> dict:
    """ Run some checks to validate user-created design in KPM.
    Return a dict of warning and error messages to be sent to the KPM.
    """
    checks = [
        _check_duplicate_ip_names,
        _check_parameters_values,
        _check_unconnected_ports_interfaces,
        _check_ext_in_to_ext_out_connections,
        _check_ambigous_ports,
        _check_externals_metanodes_types
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
