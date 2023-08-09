# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
import json
import re
from enum import Enum
from typing import NamedTuple, Union

import numexpr as ex

from .kpm_common import (
    EXT_INOUT_NAME,
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    find_connected_interfaces,
    find_dataflow_interface_by_id,
    find_dataflow_node_by_interface_id,
    find_spec_interface_by_name,
    get_dataflow_external_connections,
    get_dataflow_externals_interfaces,
    get_dataflow_ip_nodes,
    get_dataflow_ips_interfaces,
    get_dataflow_metanodes,
    get_metanode_interface_id,
    get_metanode_property_value,
)


class CheckStatus(Enum):
    OK = 0
    WARNING = 1
    ERROR = 2


class CheckResult(NamedTuple):
    status: CheckStatus
    message: Union[str, None]


def _check_duplicate_ip_names(dataflow_data, specification) -> CheckResult:
    """Check for duplicate IP core names in the design."""
    names_set = set()
    duplicates = set()
    for node in get_dataflow_ip_nodes(dataflow_data):
        if node["name"] in names_set:
            duplicates.add(node["name"])
        else:
            names_set.add(node["name"])

    if not duplicates:
        return CheckResult(CheckStatus.OK, None)
    err_msg = f"Duplicate block names: {str(list(duplicates))}"
    return CheckResult(CheckStatus.ERROR, err_msg)


def _check_parameters_values(dataflow_data, specification) -> CheckResult:
    invalid_params = list()

    for node in get_dataflow_ip_nodes(dataflow_data):
        evaluated = dict()
        for property in node["properties"]:
            param_name = property["name"]
            param_val = property["value"]
            if not re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
                try:
                    evaluated[param_name] = int(ex.evaluate(param_val, evaluated).take(0))
                except (ValueError, KeyError, SyntaxError, OverflowError):
                    invalid_params.append(f"{node['name']}:{param_name}")

    if invalid_params:
        err_msg = f"Invalid parameters values: {str(invalid_params)}"
        return CheckResult(CheckStatus.ERROR, err_msg)
    return CheckResult(CheckStatus.OK, None)


def _check_unconnected_ports_interfaces(dataflow_data, specification) -> CheckResult:
    unconn_ifaces = set(
        [
            interface["id"]
            for node in dataflow_data["graph"]["nodes"]
            for interface in node["interfaces"]
        ]
    )

    for conn in dataflow_data["graph"]["connections"]:
        unconn_ifaces.discard(conn["from"])
        unconn_ifaces.discard(conn["to"])

    if unconn_ifaces:
        unconn_ifaces_descrs = []
        for unconn_iface_id in unconn_ifaces:
            interface = find_dataflow_interface_by_id(dataflow_data, unconn_iface_id)
            unconn_ifaces_descrs.append(f"{interface['node_name']}:{interface['iface_name']}")
        return CheckResult(CheckStatus.WARNING, f"Unconnected interfaces: {unconn_ifaces_descrs}")
    return CheckResult(CheckStatus.OK, None)


def _check_ext_in_to_ext_out_connections(dataflow_data, specification) -> CheckResult:
    """Check for connections between external metanodes"""
    ext_ifaces_ids = get_dataflow_externals_interfaces(dataflow_data).keys()

    for conn in dataflow_data["graph"]["connections"]:
        if conn["from"] in ext_ifaces_ids and conn["to"] in ext_ifaces_ids:
            return CheckResult(CheckStatus.ERROR, "Existing connections between external metanodes")

    return CheckResult(CheckStatus.OK, None)


def _check_ambigous_ports(dataflow_data, specification) -> CheckResult:
    """Check for ports which are connected to another ipcore port
    and to external metanode at the same time
    """
    ext_ifaces_ids = get_dataflow_externals_interfaces(dataflow_data).keys()

    ambig_ifaces = []
    for iface_id, iface in get_dataflow_ips_interfaces(dataflow_data).items():
        iface_conns = [
            conn
            for conn in dataflow_data["graph"]["connections"]
            if conn["from"] == iface_id or conn["to"] == iface_id
        ]
        for conn in iface_conns:
            if (
                (conn["from"] in ext_ifaces_ids or conn["to"] in ext_ifaces_ids)
                and len(iface_conns)
            ) > 1:
                ambig_ifaces.append(iface)
                break

    if ambig_ifaces:
        ambig_ifaces_descrs = [
            f"{ambig_iface['node_name']}:{ambig_iface['iface_name']}"
            for ambig_iface in ambig_ifaces
        ]
        return CheckResult(
            CheckStatus.ERROR, f"External ports having >1 connections: {ambig_ifaces_descrs}"
        )
    return CheckResult(CheckStatus.OK, None)


def _check_externals_metanodes_types(dataflow_data, specification) -> CheckResult:
    """Check for external ports/interfaces which are connected to wrong type
    of external metanode. External outputs must be connected to
    `External Output` metanodes, external inputs to `External Input` etc.
    """
    bad_exts = []

    for conn in get_dataflow_external_connections(dataflow_data):
        iface_from = find_dataflow_interface_by_id(dataflow_data, conn["from"])
        iface_to = find_dataflow_interface_by_id(dataflow_data, conn["to"])
        if iface_from["iface_dir"] == "inout" and iface_to["node_name"] == EXT_OUTPUT_NAME:
            bad_exts.append(f"{iface_from['node_name']}:{iface_from['iface_name']}")
        elif iface_to["iface_dir"] == "inout" and iface_from["node_name"] == EXT_INPUT_NAME:
            bad_exts.append(f"{iface_to['node_name']}:{iface_to['iface_name']}")
        elif iface_from["iface_dir"] == "output" and iface_to["node_name"] == EXT_INOUT_NAME:
            bad_exts.append(f"{iface_from['node_name']}:{iface_from['iface_name']}")
        elif iface_to["iface_dir"] == "input" and iface_from["node_name"] == EXT_INOUT_NAME:
            bad_exts.append(f"{iface_to['node_name']}:{iface_to['iface_name']}")

    if bad_exts:
        return CheckResult(
            CheckStatus.ERROR,
            "External port/interfaces" f"connected to wrong type of external metanode: {bad_exts}",
        )
    return CheckResult(CheckStatus.OK, None)


def _check_duplicate_external_input_interfaces(dataflow_data, specification) -> CheckResult:
    """Find external input interfaces which have the same name."""
    ext_names_set = set()
    duplicates = set()

    for metanode in get_dataflow_metanodes(dataflow_data):
        if metanode["name"] != EXT_INPUT_NAME:
            continue
        for iface_id in find_connected_interfaces(
            dataflow_data, get_metanode_interface_id(metanode)
        ):
            iface = find_dataflow_interface_by_id(dataflow_data, iface_id)
            node = find_dataflow_node_by_interface_id(dataflow_data, iface_id)
            iface_type = find_spec_interface_by_name(
                specification, node["type"], iface["iface_name"]
            )["type"]

            if iface_type != "port":
                external_name = get_metanode_property_value(metanode)
                if not external_name:
                    external_name = iface["iface_name"]
                if external_name in ext_names_set:
                    duplicates.add(external_name)
                else:
                    ext_names_set.add(external_name)

    if duplicates:
        return CheckResult(
            CheckStatus.ERROR,
            "Duplicate external input interfaces names: " f"{str(list(duplicates))}",
        )
    return CheckResult(CheckStatus.OK, None)


def _check_external_inputs_missing_val(dataflow_data, specification) -> CheckResult:
    """Check for `External Input` metanodes which are connected to >1 ports
    and don't have user-specified name. Such cases would result in a valid
    design (each port would be driven separately by an external input with
    a corresponding name), but are counter intuitive, so return a warning.
    """
    err_ports = []

    for metanode in get_dataflow_metanodes(dataflow_data):
        if metanode["name"] != EXT_INPUT_NAME:
            continue
        if get_metanode_property_value(metanode):
            continue

        conn_ifaces_ids = find_connected_interfaces(
            dataflow_data, get_metanode_interface_id(metanode)
        )
        if len(conn_ifaces_ids) > 1:
            for iface_id in conn_ifaces_ids:
                iface = find_dataflow_interface_by_id(dataflow_data, iface_id)
                err_ports.append(f"{iface['node_name']}:{iface['iface_name']}")

    if err_ports:
        return CheckResult(
            CheckStatus.WARNING,
            f"External ports/interfaces {err_ports} are connected to "
            "`External Input` metanode with unspecified external name",
        )
    return CheckResult(CheckStatus.OK, None)


def _check_duplicate_external_out_inout_names(dataflow_data, specification) -> CheckResult:
    """Check for duplicate external ports/interfaces names"""
    ext_names_set = set()
    duplicates = set()

    for metanode in get_dataflow_metanodes(dataflow_data):
        if metanode["name"] == EXT_INPUT_NAME:
            continue
        # Get external port/interface name. If user didn't specify external
        # port/interface name in the textbox, let's get a corresponding
        # IP core port/interface name as default
        external_name = get_metanode_property_value(metanode)
        if not external_name:
            conn_ifaces_ids = find_connected_interfaces(
                dataflow_data, get_metanode_interface_id(metanode)
            )
            # Here we have an Input/Inout interface, which can have only 1
            # existing connection hence, we use index 0 to retrieve it
            assert len(conn_ifaces_ids) == 1
            external_name = find_dataflow_interface_by_id(dataflow_data, conn_ifaces_ids[0])[
                "iface_name"
            ]

        if external_name in ext_names_set:
            duplicates.add(external_name)
        else:
            ext_names_set.add(external_name)

    if duplicates:
        return CheckResult(
            CheckStatus.ERROR, f"Duplicate external output/inout names: {str(list(duplicates))}"
        )
    return CheckResult(CheckStatus.OK, None)


def validate_kpm_design(data: bytes, specification) -> dict:
    """Run some checks to validate user-created design in KPM.
    Return a dict of warning and error messages to be sent to the KPM.
    """
    checks = [
        _check_duplicate_ip_names,
        _check_parameters_values,
        _check_ext_in_to_ext_out_connections,
        _check_ambigous_ports,
        _check_externals_metanodes_types,
        _check_duplicate_external_input_interfaces,
        _check_external_inputs_missing_val,
        _check_duplicate_external_out_inout_names,
        _check_unconnected_ports_interfaces,
    ]

    messages = {"errors": [], "warnings": []}
    for check in checks:
        status, msg = check(json.loads(data.decode()), specification)
        if status == CheckStatus.ERROR:
            messages["errors"].append("ERROR: " + msg)
        elif status == CheckStatus.WARNING:
            messages["warnings"].append("WARNING: " + msg)

    return messages
