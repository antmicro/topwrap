# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

CONST_NAME = "Constant"
EXT_INPUT_NAME = "External Input"
EXT_OUTPUT_NAME = "External Output"
EXT_INOUT_NAME = "External Inout"


@dataclass
class InterfaceFromConnection:
    iface_id: str
    connection_id: str


@dataclass
class InterfaceData:
    node_name: str
    iface_name: str
    iface_direction: str


def get_all_graph_nodes(dataflow_json: dict) -> List[dict]:
    return _get_all_graph_values(dataflow_json, "nodes")


def get_all_graph_connections(dataflow_json: dict) -> List[dict]:
    return _get_all_graph_values(dataflow_json, "connections")


def _get_all_graph_values(dataflow_json: dict, value: str) -> List[dict]:
    """Return given value from all graphs. Example use: value="nodes" will return all nodes from all graphs"""
    all_values = []
    for graph in dataflow_json["graphs"]:
        all_values += graph[value]
    return all_values


def _get_graph_with_conn_id(dataflow_json: dict, conn_id: str) -> Optional[dict]:
    """Returns graph that has connections with given id"""
    for graph in dataflow_json["graphs"]:
        for conn in graph["connections"]:
            if conn["id"] == conn_id:
                return graph


def get_graph_with_id(dataflow_json: dict, graph_id: str) -> Optional[dict]:
    """Returns graph with given id"""
    for graph in dataflow_json["graphs"]:
        if graph["id"] == graph_id:
            return graph


def is_external_metanode(node: dict) -> bool:
    """Return True if a node is an external metanode, False otherwise."""
    return node["name"] in [EXT_INPUT_NAME, EXT_OUTPUT_NAME, EXT_INOUT_NAME]


def is_constant_metanode(node: dict) -> bool:
    """Return True if a node is a constant metanode, False otherwise."""
    return node["name"] == CONST_NAME


def is_metanode(node: dict) -> bool:
    """Return True if a node is a metanode, False otherwise."""
    return is_external_metanode(node) or is_constant_metanode(node)


def is_subgraph_node(node: dict) -> bool:
    """Return True if a node is a subgraph node, False otherwise."""
    return "subgraph" in node.keys()


def get_dataflow_ip_nodes(dataflow_json: dict) -> List[dict]:
    """Return a list of nodes which represent ip cores
    (i.e. filter out External Outputs, Inputs and Inouts)
    """
    ip_nodes = []
    for node in get_all_graph_nodes(dataflow_json):
        if not is_metanode(node) and not is_subgraph_node(node):
            ip_nodes.append(node)
    return ip_nodes


def get_dataflow_subgraph_nodes(dataflow_json: dict) -> List[dict]:
    """Return subgraph nodes from every graph. Subgraph node is a node that has "subgraph" field"""
    return [node for node in get_all_graph_nodes(dataflow_json) if is_subgraph_node(node)]


def get_dataflow_external_metanodes(dataflow_json: dict) -> List[dict]:
    """Return a list of external metanodes (i.e. External Outputs and Inputs)"""
    return [node for node in get_all_graph_nodes(dataflow_json) if is_external_metanode(node)]


def get_dataflow_constant_metanodes(dataflow_json: dict) -> List[dict]:
    """Return a list of constant metanodes"""
    return [node for node in get_all_graph_nodes(dataflow_json) if is_constant_metanode(node)]


def _get_interfaces(nodes: List[dict]) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces belonging to given nodes.
    The resulting dict consists of items:
    {"iface_id": [InterfaceData]}
    There can be multiple interfaces with given id"""
    result = defaultdict(list)
    for node in nodes:
        for interface in node["interfaces"]:
            result[interface["id"]].append(
                InterfaceData(node["instanceName"], interface["name"], interface["direction"])
            )
    return result


def get_dataflow_ips_interfaces(dataflow_json: dict) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces of all the nodes representing
    ip cores. The resulting dict consists of items
    {"iface_id": [InterfaceData]}"""

    return _get_interfaces(get_dataflow_ip_nodes(dataflow_json))


def get_dataflow_ip_connections(dataflow_json: dict) -> List[dict]:
    """Return connections between two IP cores
    (e.g. filter out connections to external metanodes)
    """
    ifaces_ids = get_dataflow_ips_interfaces(dataflow_json).keys()
    graph_ip_connections = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] in ifaces_ids and conn["to"] in ifaces_ids:
            graph_ip_connections.append(conn)
    return graph_ip_connections


def get_dataflow_external_interfaces(dataflow_json: dict) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces of all the external metanodes.
    The resulting dict consists of items
    {"iface_id": [InterfaceData]}"""
    return _get_interfaces(get_dataflow_external_metanodes(dataflow_json))


def get_dataflow_constant_interfaces(dataflow_json: dict) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces of all the constant metanodes.
    The resulting dict consists of items
    { "iface_id": [InterfaceData]}"""
    return _get_interfaces(get_dataflow_constant_metanodes(dataflow_json))


def _get_ifaces_metanodes_connections(dataflow_json: dict, ifaces_ids: List[str]) -> List[dict]:
    """Return all connections in which one of the connection node id is in "ifaces_ids" """
    graph_connections = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] in ifaces_ids or conn["to"] in ifaces_ids:
            graph_connections.append(conn)
    return graph_connections


def get_dataflow_external_connections(dataflow_json: dict) -> List[dict]:
    """Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_external_interfaces(dataflow_json).keys()
    return _get_ifaces_metanodes_connections(dataflow_json, list(ifaces_ids))


def get_dataflow_constant_connections(dataflow_json: dict) -> List[dict]:
    """Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_constant_interfaces(dataflow_json).keys()
    return _get_ifaces_metanodes_connections(dataflow_json, list(ifaces_ids))


def get_metanode_interface_id(metanode: dict) -> str:
    """Return given metanode's interface id. Metanodes always have exactly 1
    interface, so it suffices to take 0th element of the "interfaces" array.
    """
    return metanode["interfaces"][0]["id"]


def get_metanode_property_value(metanode: dict) -> str:
    """Return a value stored in an external metanode textbox.
    Metanodes always have exactly one property, so it suffices to take
    0th element of the "properties" array.
    """
    return metanode["properties"][0]["value"]


def find_dataflow_node_by_interface_name_id(
    dataflow_json: dict, iface_name: str, iface_id: str
) -> Optional[dict]:
    """Return dataflow node which has an `iface_name` interface.
    Note that there can be multiple interfaces with given id so finding node by interface id is not reliable
    """
    for node in get_all_graph_nodes(dataflow_json):
        for interface in node["interfaces"]:
            if interface["name"] == iface_name and interface["id"] == iface_id:
                return node


def find_dataflow_interface_by_id(
    dataflow_json: dict, iface_conn: InterfaceFromConnection
) -> Optional[InterfaceData]:
    """Return InterfaceData object that corresponds to a given 'iface_id'"""
    graph_with_connection = _get_graph_with_conn_id(dataflow_json, iface_conn.connection_id)
    if graph_with_connection is None:
        raise ValueError(f"Graph with connection {iface_conn.connection_id} was not found")

    graph_interfaces = _get_interfaces(graph_with_connection["nodes"])
    if iface_conn.iface_id in graph_interfaces.keys():
        if len(graph_interfaces[iface_conn.iface_id]) > 1:
            logging.warning(
                f"Multiple instances with id {iface_conn.iface_id} were found in connection {iface_conn.connection_id}"
            )
        return graph_interfaces[iface_conn.iface_id][0]


def find_spec_interface_by_name(
    specification: dict, node_type: str, iface_name: str
) -> Optional[dict]:
    """Find `name` interface of `ip_type` IP core in `specification`"""
    for node in specification["nodes"]:
        if node["layer"] != node_type:
            continue
        for interface in node["interfaces"]:
            if interface["name"] == iface_name:
                return interface


def find_dataflow_node_type_by_name(dataflow_data: dict, node_name: str) -> Optional[str]:
    for node in get_all_graph_nodes(dataflow_data):
        if node["instanceName"] == node_name:
            return node["name"]


def find_connected_interfaces(dataflow_json: dict, iface_id: str) -> List[InterfaceFromConnection]:
    """Return a list of InterfacefromConnection objects where 'iface_id' is referenced in a connection"""
    result = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] == iface_id:
            result.append(InterfaceFromConnection(conn["to"], conn["id"]))
        elif conn["to"] == iface_id:
            result.append(InterfaceFromConnection(conn["from"], conn["id"]))
    return result
