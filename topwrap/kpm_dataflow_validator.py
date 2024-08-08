# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from typing import NamedTuple, Union

import numexpr as ex
from pipeline_manager_backend_communication.misc_structures import MessageType

from .kpm_common import (
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    InterfaceFromConnection,
    find_connected_interfaces,
    find_dataflow_interface_by_id,
    find_dataflow_node_by_interface_name_id,
    find_spec_interface_by_name,
    get_all_graph_connections,
    get_all_graph_nodes,
    get_dataflow_constant_metanodes,
    get_dataflow_external_interfaces,
    get_dataflow_external_metanodes,
    get_dataflow_ip_connections,
    get_dataflow_ip_nodes,
    get_dataflow_ips_interfaces,
    get_metanode_interface_id,
    get_metanode_property_value,
)


class CheckResult(NamedTuple):
    status: MessageType
    message: Union[str, None]


def _check_duplicate_ip_names(dataflow_data, specification) -> CheckResult:
    """Check for duplicate IP core names in the design."""

    names_set = set()
    duplicates = set()
    for node in get_dataflow_ip_nodes(dataflow_data):
        if node["instanceName"] in names_set:
            duplicates.add(node["instanceName"])
        else:
            names_set.add(node["instanceName"])

    if not duplicates:
        return CheckResult(MessageType.OK, None)
    err_msg = f"Duplicate block names: {str(list(duplicates))}"
    return CheckResult(MessageType.ERROR, err_msg)


def _check_parameters_values(dataflow_data, specification) -> CheckResult:
    invalid_params = list()
    for node in get_dataflow_ip_nodes(dataflow_data):
        evaluated = dict()
        for property in node["properties"]:
            param_name = property["name"]
            param_val = property["value"]

            if isinstance(param_val, int):
                continue

            if not re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
                try:
                    evaluated[param_name] = int(ex.evaluate(param_val, evaluated).take(0))
                except (ValueError, KeyError, SyntaxError, OverflowError):
                    invalid_params.append(f"{node['name']}:{param_name}")

    for node in get_dataflow_constant_metanodes(dataflow_data):
        name = node["properties"][0]["name"]
        value = node["properties"][0]["value"]

        try:
            int(value, base=0)
        except ValueError:
            invalid_params.append(f"{name}:{value}")

    if invalid_params:
        err_msg = f"Invalid parameters values: {str(invalid_params)}"
        return CheckResult(MessageType.ERROR, err_msg)
    return CheckResult(MessageType.OK, None)


def _check_unconnected_ports_interfaces(dataflow_data, specification) -> CheckResult:
    unconn_ifaces = set(
        [
            interface["id"]
            for node in get_all_graph_nodes(dataflow_data)
            for interface in node["interfaces"]
        ]
    )

    for conn in get_all_graph_connections(dataflow_data):
        unconn_ifaces.discard(conn["from"])
        unconn_ifaces.discard(conn["to"])

    if unconn_ifaces:
        unconn_ifaces_descrs = []
        for unconn_iface_id in unconn_ifaces:
            unconn_ifaces_descrs.append(f"{unconn_iface_id}")
        return CheckResult(MessageType.WARNING, f"Unconnected interfaces: {unconn_ifaces_descrs}")
    return CheckResult(MessageType.OK, None)


def _check_ext_in_to_ext_out_connections(dataflow_data, specification) -> CheckResult:
    """Check for connections between external metanodes"""
    ext_ifaces_ids = get_dataflow_external_interfaces(dataflow_data).keys()

    for conn in get_all_graph_connections(dataflow_data):
        if conn["from"] in ext_ifaces_ids and conn["to"] in ext_ifaces_ids:
            return CheckResult(MessageType.ERROR, "Existing connections between external metanodes")

    return CheckResult(MessageType.OK, None)


def _check_ambigous_ports(dataflow_data, specification) -> CheckResult:
    """Check for ports which are connected to another ipcore port
    and to external metanode at the same time
    """
    ext_ifaces_ids = get_dataflow_external_interfaces(dataflow_data).keys()

    ambig_ifaces = []
    for iface_id, iface in get_dataflow_ips_interfaces(dataflow_data).items():
        iface_conns = [
            conn
            for conn in get_all_graph_connections(dataflow_data)
            if conn["from"] == iface_id or conn["to"] == iface_id
        ]
        for conn in iface_conns:
            if (conn["from"] in ext_ifaces_ids or conn["to"] in ext_ifaces_ids) and len(
                iface_conns
            ) > 1:
                ambig_ifaces.append(iface[0])
                break

    if ambig_ifaces:
        ambig_ifaces_descrs = [
            f"{ambig_iface.node_name}:{ambig_iface.iface_name}" for ambig_iface in ambig_ifaces
        ]
        return CheckResult(
            MessageType.ERROR, f"External ports having >1 connections: {ambig_ifaces_descrs}"
        )
    return CheckResult(MessageType.OK, None)


def _check_duplicate_external_input_interfaces(dataflow_data, specification) -> CheckResult:
    """Find external input interfaces which have the same name."""
    ext_names_set = set()
    duplicates = set()

    for metanode in get_dataflow_external_metanodes(dataflow_data):
        if metanode["instanceName"] != EXT_INPUT_NAME:
            continue
        for iface_conn in find_connected_interfaces(
            dataflow_data, get_metanode_interface_id(metanode)
        ):
            iface = find_dataflow_interface_by_id(dataflow_data, iface_conn)
            if iface is None:
                raise ValueError(
                    f"Interface with id {iface_conn.iface_id} was not found in connection {iface_conn.connection_id}"
                )

            node = find_dataflow_node_by_interface_name_id(
                dataflow_data, iface.iface_name, iface_conn.iface_id
            )
            if node is None:
                raise ValueError(
                    f"Node with interface name {iface.iface_name} and interface id {iface_conn.iface_id} was not found"
                )

            iface_types = find_spec_interface_by_name(specification, node["name"], iface.iface_name)
            if iface_types is None:
                raise ValueError(f"Interface {iface.iface_name} was not found in specification")

            iface_types = iface_types["type"]

            if "port" not in iface_types:
                external_name = get_metanode_property_value(metanode)
                if not external_name:
                    external_name = iface.iface_name
                if external_name in ext_names_set:
                    duplicates.add(external_name)
                else:
                    ext_names_set.add(external_name)

    if duplicates:
        return CheckResult(
            MessageType.ERROR,
            "Duplicate external input interfaces names: " f"{str(list(duplicates))}",
        )
    return CheckResult(MessageType.OK, None)


def _check_external_inputs_missing_val(dataflow_data, specification) -> CheckResult:
    """Check for `External Input` metanodes which are connected to >1 ports
    and don't have user-specified name. Such cases would result in a valid
    design (each port would be driven separately by an external input with
    a corresponding name), but are counter intuitive, so return a warning.
    """
    err_ports = []

    for metanode in get_dataflow_external_metanodes(dataflow_data):
        if metanode["instanceName"] != EXT_INPUT_NAME:
            continue
        if get_metanode_property_value(metanode):
            continue

        conn_ifaces_ids = find_connected_interfaces(
            dataflow_data, get_metanode_interface_id(metanode)
        )
        if len(conn_ifaces_ids) > 1:
            for iface_conn in conn_ifaces_ids:
                iface = find_dataflow_interface_by_id(dataflow_data, iface_conn)
                if iface is None:
                    raise ValueError(
                        f"Interface {iface_conn.iface_id} is used in connection {iface_conn.connection_id} but is not defined"
                    )
                err_ports.append(f"{iface.node_name}:{iface.iface_name}")

    if err_ports:
        return CheckResult(
            MessageType.WARNING,
            f"External ports/interfaces {err_ports} are connected to "
            "`External Input` metanode with unspecified external name",
        )
    return CheckResult(MessageType.OK, None)


def _check_duplicate_external_out_names(dataflow_data, specification) -> CheckResult:
    """Check for duplicate names of external outputs"""
    ext_names_set = set()
    duplicates = set()

    for metanode in get_dataflow_external_metanodes(dataflow_data):
        if metanode["instanceName"] == EXT_OUTPUT_NAME:
            # Get external port/interface name. If user didn't specify external
            # port/interface name in the textbox, let's get a corresponding
            # IP core port/interface name as default
            external_name = get_metanode_property_value(metanode)
            if not external_name:
                conn_ifaces_ids = find_connected_interfaces(
                    dataflow_data, get_metanode_interface_id(metanode)
                )
                if not conn_ifaces_ids:
                    continue
                # Here we have an Input interface, which can have only 1
                # existing connection hence, we use index 0 to retrieve it
                assert len(conn_ifaces_ids) == 1
                external_interface = find_dataflow_interface_by_id(
                    dataflow_data, conn_ifaces_ids[0]
                )
                if external_interface is None:
                    raise ValueError(
                        f"Interface {conn_ifaces_ids[0].iface_id} was not found in connection {conn_ifaces_ids[0].connection_id}"
                    )
                external_name = external_interface.iface_name

            if external_name in ext_names_set:
                duplicates.add(external_name)
            else:
                ext_names_set.add(external_name)

    if duplicates:
        return CheckResult(
            MessageType.ERROR, f"Duplicate external output names: {str(list(duplicates))}"
        )
    return CheckResult(MessageType.OK, None)


def _check_inouts_connections(dataflow_data, specification) -> CheckResult:
    """Check for connections between ports where one of them has `inout` direction.
    Return a warning if such connections exist.
    """
    connected_inouts = []
    for connection in get_dataflow_ip_connections(dataflow_data):
        iface_from = find_dataflow_interface_by_id(
            dataflow_data, InterfaceFromConnection(connection["from"], connection["id"])
        )
        if iface_from is None:
            raise ValueError(
                f"Interface with id {connection['from']} was not found in connection {connection['id']}"
            )

        iface_to = find_dataflow_interface_by_id(
            dataflow_data, InterfaceFromConnection(connection["to"], connection["id"])
        )
        if iface_to is None:
            raise ValueError(
                f"Interface with id {connection['to']} was not found in connection {connection['id']}"
            )

        if iface_from.iface_direction == "inout":
            connected_inouts.append(f"{iface_from.node_name}:{iface_from.iface_name}")
        if iface_to.iface_direction == "inout":
            connected_inouts.append(f"{iface_to.node_name}:{iface_to.iface_name}")

    if connected_inouts:
        return CheckResult(
            MessageType.WARNING,
            f"Wires connecting inout ports {connected_inouts} are always "
            "external in the top module by Amaranth",
        )
    return CheckResult(MessageType.OK, None)


def validate_kpm_design(data: dict, specification: dict) -> dict:
    """Run some checks to validate user-created design in KPM.
    Return a dict of warning and error messages to be sent to the KPM.
    """
    checks = [
        _check_duplicate_ip_names,
        _check_parameters_values,
        _check_ext_in_to_ext_out_connections,
        _check_ambigous_ports,
        _check_duplicate_external_input_interfaces,
        _check_external_inputs_missing_val,
        _check_duplicate_external_out_names,
        _check_unconnected_ports_interfaces,
        _check_inouts_connections,
    ]

    messages = {"errors": [], "warnings": []}
    for check in checks:
        status, msg = check(data, specification)
        if status == MessageType.ERROR:
            messages["errors"].append(msg)
        elif status == MessageType.WARNING:
            messages["warnings"].append(msg)

    return messages
