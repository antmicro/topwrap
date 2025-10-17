# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from topwrap.hdl_parsers_utils import PortDirection
from topwrap.model.design import Design
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module
from topwrap.util import UnreachableError

from .util import JsonType

SPECIFICATION_VERSION = "20250623.14"
CONST_NAME = "Constant"
SUBGRAPH_METANODE = "Subgraph port"
EXT_INPUT_NAME = "External Input"
EXT_OUTPUT_NAME = "External Output"
EXT_INOUT_NAME = "External Inout"
SUBGRAPH_NODE = "subgraph"
EXPOSED_IFACE = "externalName"
METANODE_CATEGORY = "Metanode"


@dataclass
class InterfaceFromConnection:
    iface_id: str
    connection_id: str


@dataclass
class InterfaceData:
    node_name: str
    iface_name: str
    iface_direction: str


@dataclass
class RPCparams:
    host: str
    port: int
    specification: JsonType
    build_dir: Path
    design: Optional[Design]
    modules: list[Module]
    interfaces: list[InterfaceDefinition]


def get_all_graph_nodes(dataflow_json: JsonType) -> List[JsonType]:
    return _get_all_graph_values(dataflow_json, "nodes")


def get_all_graph_connections(dataflow_json: JsonType) -> List[Dict[str, str]]:
    return _get_all_graph_values(dataflow_json, "connections")


def _get_all_graph_values(dataflow_json: JsonType, value: str) -> List[JsonType]:
    """Return given value from all graphs. Example use: value="nodes" will return all nodes from all
    graphs"""
    all_values = []
    for graph in dataflow_json["graphs"]:
        all_values += graph[value]
    return all_values


def _get_graph_with_conn_id(dataflow_json: JsonType, conn_id: str) -> Optional[JsonType]:
    """Returns graph that has connections with given id"""
    for graph in dataflow_json["graphs"]:
        for conn in graph["connections"]:
            if conn["id"] == conn_id:
                return graph


def get_graph_with_id(dataflow_json: JsonType, graph_id: str) -> Optional[JsonType]:
    """Returns graph with given id"""
    for graph in dataflow_json["graphs"]:
        if graph["id"] == graph_id:
            return graph


def get_entry_graph(dataflow_json: JsonType) -> JsonType:
    """Returns the "entry" graph of the dataflow (the top level one)"""

    # if there is no "entryGraph" defined then there is only one graph in the design
    graph = get_graph_with_id(
        dataflow_json, dataflow_json.get("entryGraph", dataflow_json["graphs"][0]["id"])
    )
    if graph is None:
        raise UnreachableError
    return graph


def graph_to_isolated_dataflow(dataflow: JsonType, graph_id: str) -> JsonType:
    return {
        "version": dataflow.get("version"),
        "graphs": [get_graph_with_id(dataflow, graph_id)],
        "metadata": dataflow.get("metadata"),
    }


def kpm_direction_to_port_dir(kpm_dir: str) -> PortDirection:
    return {"input": PortDirection.IN, "output": PortDirection.OUT, "inout": PortDirection.INOUT}[
        kpm_dir
    ]


def is_external_metanode(node: JsonType) -> bool:
    """Return True if a node is an external metanode, False otherwise."""
    return node["name"] in [EXT_INPUT_NAME, EXT_OUTPUT_NAME, EXT_INOUT_NAME]


def is_constant_metanode(node: JsonType) -> bool:
    """Return True if a node is a constant metanode, False otherwise."""
    return node["name"] == CONST_NAME


def is_subgraph_metanode(node: JsonType) -> bool:
    """Return True if a node is a subgraph metanode, False otherwise."""
    return node["name"] == SUBGRAPH_METANODE


def is_metanode(node: JsonType) -> bool:
    """Return True if a node is a metanode, False otherwise."""
    return is_external_metanode(node) or is_constant_metanode(node) or is_subgraph_metanode(node)


def is_subgraph_node(node: JsonType) -> bool:
    """Return True if a node is a subgraph node, False otherwise."""
    return SUBGRAPH_NODE in node.keys()


def is_exposed_iface(iface: JsonType) -> bool:
    """Return True if a interface is exposed in some subgraph node, False otherwise."""
    return EXPOSED_IFACE in iface.keys()


def is_kpm_interface_a_topwrap_interface(node: JsonType, port_name: str, spec: JsonType) -> bool:
    """Check whether a port on a node represents a topwrap interface"""

    if is_subgraph_node(node):
        return False

    spec_interface = find_spec_interface_by_name(spec, node["name"], port_name)
    if spec_interface is None:
        raise ValueError(
            f'Interface "{port_name}" of IP "{node["name"]}" was not found in the specification'
        )

    return spec_interface["type"] != ["port"]


def _get_subgraph_metanode_iface(subgraph_metanode: JsonType, exposed: bool) -> JsonType:
    for idx, interface in enumerate(subgraph_metanode["interfaces"]):
        if is_exposed_iface(interface):
            # Subgraph metanodes have two ports - the external subgraph reference and the second one
            # will the connections of subgraph port
            # Because of this the "connection subgraph iface" will always be at the index "opposite"
            # (idx + 1) % 2 from the one with "externalName"
            iface_index = idx
            if not exposed:
                iface_index = (idx + 1) % 2
            return subgraph_metanode["interfaces"][iface_index]
    raise ValueError(
        f"Subgraph metanode with id {subgraph_metanode['id']} doesn't have exposed interface"
    )


def get_exposed_subgraph_meta_iface(subgraph_metanode: JsonType) -> JsonType:
    return _get_subgraph_metanode_iface(subgraph_metanode, True)


def get_unexposed_subgraph_meta_iface(subgraph_metanode: JsonType) -> JsonType:
    return _get_subgraph_metanode_iface(subgraph_metanode, False)


def get_dataflow_subgraph_metanodes(dataflow_json: JsonType) -> List[JsonType]:
    """Return a list of subgraph metanodes"""
    subgraph_metanodes = []
    for node in get_all_graph_nodes(dataflow_json):
        if is_subgraph_metanode(node):
            subgraph_metanodes.append(node)
    return subgraph_metanodes


def get_dataflow_current_hierarchy_ip_nodes(dataflow_json: JsonType) -> List[JsonType]:
    """Return a list of nodes which represent ip cores and are not subgraph nodes
    (i.e. filter out External Outputs, Inputs and Inouts)
    """
    ip_nodes = []
    for node in get_all_graph_nodes(dataflow_json):
        if not is_metanode(node) and not is_subgraph_node(node):
            ip_nodes.append(node)
    return ip_nodes


def get_dataflow_subgraph_nodes(dataflow_json: JsonType) -> List[JsonType]:
    """Return subgraph nodes from every graph. Subgraph node is a node that has "subgraph" field"""
    return [node for node in get_all_graph_nodes(dataflow_json) if is_subgraph_node(node)]


def get_dataflow_external_metanodes(dataflow_json: JsonType) -> List[JsonType]:
    """Return a list of external metanodes (i.e. External Outputs and Inputs)"""
    return [node for node in get_all_graph_nodes(dataflow_json) if is_external_metanode(node)]


def get_dataflow_constant_metanodes(dataflow_json: JsonType) -> List[JsonType]:
    """Return a list of constant metanodes"""
    return [node for node in get_all_graph_nodes(dataflow_json) if is_constant_metanode(node)]


def _get_interfaces(nodes: List[JsonType]) -> Dict[str, List[InterfaceData]]:
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


def get_dataflow_ips_interfaces(dataflow_json: JsonType) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces of all the nodes representing ip cores.
    The resulting dict consists of items:
    {"iface_id": [InterfaceData]}"""

    return _get_interfaces(get_dataflow_current_hierarchy_ip_nodes(dataflow_json))


def get_dataflow_subgraph_meta_interfaces(
    dataflow_json: JsonType,
) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all subgraph metanodes interfaces.
    The resulting dict consists of items:
    {"iface_id": [InterfaceData]}"""

    return _get_interfaces(get_dataflow_subgraph_metanodes(dataflow_json))


def get_dataflow_subgraph_meta_connections(dataflow_json: JsonType) -> List[Dict[str, str]]:
    """Return connections that are related to subgraph metanodes"""
    ifaces_ids = get_dataflow_subgraph_meta_interfaces(dataflow_json).keys()
    subgraph_connections = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] in ifaces_ids and conn["to"] in ifaces_ids:
            subgraph_connections.append(conn)
    return subgraph_connections


def get_dataflow_ip_connections(dataflow_json: JsonType) -> List[Dict[str, str]]:
    """Return connections between two IP cores
    (e.g. filter out connections to external metanodes)
    """
    ifaces_ids = get_dataflow_ips_interfaces(dataflow_json).keys()
    graph_ip_connections = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] in ifaces_ids and conn["to"] in ifaces_ids:
            graph_ip_connections.append(conn)
    return graph_ip_connections


def get_dataflow_external_interfaces(dataflow_json: JsonType) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces of all the external metanodes.
    The resulting dict consists of items
    {"iface_id": [InterfaceData]}"""
    return _get_interfaces(get_dataflow_external_metanodes(dataflow_json))


def get_dataflow_constant_interfaces(dataflow_json: JsonType) -> Dict[str, List[InterfaceData]]:
    """Return a dict of all the interfaces of all the constant metanodes.
    The resulting dict consists of items
    {"iface_id": [InterfaceData]}"""
    return _get_interfaces(get_dataflow_constant_metanodes(dataflow_json))


def _get_ifaces_metanodes_connections(
    dataflow_json: JsonType, ifaces_ids: List[str]
) -> List[Dict[str, str]]:
    """Return all connections in which one of the connection node id is in "ifaces_ids" """
    graph_connections = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] in ifaces_ids or conn["to"] in ifaces_ids:
            graph_connections.append(conn)
    return graph_connections


def get_dataflow_external_connections(dataflow_json: JsonType) -> List[JsonType]:
    """Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_external_interfaces(dataflow_json).keys()
    return _get_ifaces_metanodes_connections(dataflow_json, list(ifaces_ids))


def get_dataflow_constant_connections(dataflow_json: JsonType) -> List[JsonType]:
    """Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_constant_interfaces(dataflow_json).keys()
    return _get_ifaces_metanodes_connections(dataflow_json, list(ifaces_ids))


def get_metanode_interface_id(metanode: JsonType) -> str:
    """Return given metanode's interface id. Metanodes always have exactly 1
    interface, so it suffices to take 0th element of the "interfaces" array.
    """
    return metanode["interfaces"][0]["id"]


def get_metanode_property_value(metanode: JsonType) -> str:
    """Return a value stored in an external metanode textbox.
    Metanodes always have exactly one property, so it suffices to take
    0th element of the "properties" array.
    """
    return metanode["properties"][0]["value"]


def get_external_metanode_direction(metanode: JsonType) -> PortDirection:
    """Gets a PortDirection of the external or subgraph port metanode"""

    if is_subgraph_metanode(metanode):
        dir = get_exposed_subgraph_meta_iface(metanode)["direction"]
        return kpm_direction_to_port_dir(dir)
    elif is_external_metanode(metanode):
        return {
            EXT_INPUT_NAME: PortDirection.IN,
            EXT_OUTPUT_NAME: PortDirection.OUT,
            EXT_INOUT_NAME: PortDirection.INOUT,
        }[metanode["name"]]
    else:
        raise ValueError("Neither an external nor a subgraph port metanode")


def find_dataflow_node_by_interface_name_id(
    dataflow_json: JsonType, iface_name: str, iface_id: str
) -> Optional[JsonType]:
    """Return dataflow node which has an `iface_name` interface.
    Note that there can be multiple interfaces with given id so finding node by interface id is not
    reliable
    """
    for node in get_all_graph_nodes(dataflow_json):
        for interface in node["interfaces"]:
            if interface["name"] == iface_name and interface["id"] == iface_id:
                return node


def find_dataflow_interface_by_id(
    dataflow_json: JsonType, iface_conn: InterfaceFromConnection
) -> Optional[InterfaceData]:
    """Return InterfaceData object that corresponds to a given 'iface_id'"""
    graph_with_connection = _get_graph_with_conn_id(dataflow_json, iface_conn.connection_id)
    if graph_with_connection is None:
        raise ValueError(f"Graph with connection {iface_conn.connection_id} was not found")

    graph_interfaces = _get_interfaces(graph_with_connection["nodes"])
    if iface_conn.iface_id in graph_interfaces.keys():
        if len(graph_interfaces[iface_conn.iface_id]) > 1:
            logging.warning(
                f"Multiple instances with id {iface_conn.iface_id} were found in connection"
                f" {iface_conn.connection_id}"
            )
        return graph_interfaces[iface_conn.iface_id][0]


def get_interfaces_from_connection(
    dataflow_json: JsonType, conn: Dict[str, str]
) -> Tuple[Optional[InterfaceData], Optional[InterfaceData]]:
    iface_from = find_dataflow_interface_by_id(
        dataflow_json, InterfaceFromConnection(conn["from"], conn["id"])
    )

    iface_to = find_dataflow_interface_by_id(
        dataflow_json, InterfaceFromConnection(conn["to"], conn["id"])
    )
    return iface_from, iface_to


def find_spec_interface_by_name(
    specification: JsonType, node_type: str, iface_name: str
) -> Optional[JsonType]:
    """Find `name` interface of `ip_type` IP core in `specification`"""
    for node in specification["nodes"]:
        if node["name"] != node_type:
            continue
        for interface in node["interfaces"]:
            if interface["name"] == iface_name:
                return interface


def find_connected_interfaces(
    dataflow_json: JsonType, iface_id: str
) -> List[InterfaceFromConnection]:
    """Return a list of InterfaceFromConnection objects where 'iface_id' is referenced in a
    connection"""
    result = []
    for conn in get_all_graph_connections(dataflow_json):
        if conn["from"] == iface_id:
            result.append(InterfaceFromConnection(conn["to"], conn["id"]))
        elif conn["to"] == iface_id:
            result.append(InterfaceFromConnection(conn["from"], conn["id"]))
    return result


def get_graph_id_from_node(dataflow_json: JsonType, node_id: str) -> str:
    """Return id of graph where given node exists"""
    for graph in dataflow_json["graphs"]:
        for node in graph["nodes"]:
            if node["id"] == node_id:
                return graph["id"]
    raise ValueError(f"Node id {id} doesn't exist")


def get_graph_id_name(dataflow_data: JsonType, graph_id: str) -> Optional[str]:
    """Return name of graph with given id. Note that root graph does not have name"""
    for node in get_all_graph_nodes(dataflow_data):
        if node.get("subgraph") == graph_id:
            return node["instanceName"]


def check_for_iface_in_conn_graph(dataflow_json: JsonType, iface_id: str, graph_id: str) -> bool:
    """Checks if in any connection of graph with specified id exists connection with the provided
    `iface_id`"""
    for graph in dataflow_json["graphs"]:
        if graph["id"] == graph_id:
            for conn in graph["connections"]:
                if iface_id in [conn["from"], conn["to"]]:
                    return True
            return False
    raise ValueError(f"Graph with id {id} doesn't exist")


def error_connections(node: bool, id: str) -> ValueError:
    return ValueError(
        "While parsing graph connections, "
        + ("node with an interface " if node else "interface ")
        + f"with the id {id} was not found"
    )
