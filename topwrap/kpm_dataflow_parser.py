# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Set, Tuple

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import KPMDataflowSubgraphnode

from .kpm_common import (
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    InterfaceData,
    InterfaceFromConnection,
    find_dataflow_interface_by_id,
    find_dataflow_node_by_interface_name_id,
    find_dataflow_node_type_by_name,
    find_spec_interface_by_name,
    get_all_graph_nodes,
    get_dataflow_constant_connections,
    get_dataflow_external_connections,
    get_dataflow_ip_connections,
    get_dataflow_ip_nodes,
    get_dataflow_subgraph_nodes,
    get_graph_with_id,
    get_metanode_property_value,
    is_constant_metanode,
    is_external_metanode,
    is_metanode,
)
from .util import recursive_defaultdict, recursive_defaultdict_to_dict


@dataclass
class ConnectionData:
    iface_to: InterfaceData
    iface_from: InterfaceData
    node_to: dict
    node_from: dict


def _parse_value_width_parameter(param: str) -> dict:
    """`param` is a string representing a bit vector in Verilog format
    (e.g. "16'h5A5A") which is parsed to a value/width parameter
    """
    quote_pos = param.find("'")
    width = param[:quote_pos]
    radix = param[quote_pos + 1]
    value = param[quote_pos + 2 :]
    radix_to_base = {"h": 16, "d": 10, "o": 8, "b": 2}

    return {"value": int(value, radix_to_base[radix]), "width": int(width)}


def _kpm_properties_to_parameters(properties: dict) -> dict:
    """Parse `properties` taken from a dataflow node into
    Topwrap's IP core's parameters.
    """
    result = dict()
    for property in properties:
        param_name = property["name"]
        param_val = property["value"]
        if re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
            result[param_name] = _parse_value_width_parameter(param_val)
            continue

        try:
            result[param_name] = int(param_val, base=0)
        except ValueError:
            result[param_name] = param_val

    return result


def _kpm_nodes_to_parameters(dataflow_data) -> dict:
    result = dict()
    for node in get_dataflow_ip_nodes(dataflow_data):
        result[node["instanceName"]] = _kpm_properties_to_parameters(node["properties"])
    return result


def _kpm_nodes_to_ips(dataflow_data: dict, specification: dict) -> dict:
    """Parse dataflow nodes into Topwrap's "ips" section
    of a design description yaml
    """
    ips = {}
    filename = None
    for node in get_dataflow_ip_nodes(dataflow_data):
        for spec_node in specification["nodes"]:
            if spec_node["layer"] == node["name"]:
                filename = spec_node["additionalData"]

        if filename is None:
            raise ValueError("Ip file was not found")
        ips[node["instanceName"]] = {
            "file": filename,
        }
    return ips


def _get_conn_ifaces_and_nodes(conn: dict, dataflow_data: dict) -> ConnectionData:
    iface_to = find_dataflow_interface_by_id(
        dataflow_data, InterfaceFromConnection(conn["to"], conn["id"])
    )
    if iface_to is None:
        raise ValueError(f"Interface with id {conn['to']} was not found")

    iface_from = find_dataflow_interface_by_id(
        dataflow_data, InterfaceFromConnection(conn["from"], conn["id"])
    )
    if iface_from is None:
        raise ValueError(f"Interface with id {conn['from']} was not found")

    node_to = find_dataflow_node_by_interface_name_id(
        dataflow_data, iface_to.iface_name, conn["to"]
    )
    if node_to is None:
        raise ValueError(f"Node with id {conn['to']} was not found")

    node_from = find_dataflow_node_by_interface_name_id(
        dataflow_data, iface_from.iface_name, conn["from"]
    )
    if node_from is None:
        raise ValueError(f"Node with id {conn['from']} was not found")

    return ConnectionData(iface_to, iface_from, node_to, node_from)


def _kpm_connections_to_ports_ifaces(dataflow_data: dict, specification: dict) -> dict:
    """Parse dataflow connections between nodes representing IP cores into
    "ports" and "interfaces" sections of a Topwrap's design description yaml
    """
    ports_conns = recursive_defaultdict()
    interfaces_conns = recursive_defaultdict()

    for conn in get_dataflow_ip_connections(dataflow_data):
        iface_from = find_dataflow_interface_by_id(
            dataflow_data, InterfaceFromConnection(conn["from"], conn["id"])
        )
        if iface_from is None:
            raise ValueError(f"Interface with id {conn['id']} was not found")

        iface_to = find_dataflow_interface_by_id(
            dataflow_data, InterfaceFromConnection(conn["to"], conn["id"])
        )
        if iface_to is None:
            raise ValueError(f"Interface with id {conn['id']} was not found")

        node_to_type = find_dataflow_node_type_by_name(dataflow_data, iface_to.node_name)
        if node_to_type is None:
            raise ValueError(f"Node with {iface_to.node_name} was not found")

        if node_to_type == KPMDataflowSubgraphnode.DUMMY_NAME_BASE:
            iface_to_types = ["port"]
        else:
            interface_in_spec = find_spec_interface_by_name(
                specification, node_to_type, iface_to.iface_name
            )
            if interface_in_spec is None:
                raise ValueError(
                    f"Interface {iface_to.iface_name} was not found in {node_to_type} in specification"
                )
            iface_to_types = interface_in_spec["type"]

        if "port" in iface_to_types:
            conns_dict = ports_conns
        else:
            conns_dict = interfaces_conns

        conns_dict[iface_to.node_name][iface_to.iface_name] = (
            iface_from.node_name,
            iface_from.iface_name,
        )

    ports_conns = recursive_defaultdict_to_dict(ports_conns)
    interfaces_conns = recursive_defaultdict_to_dict(interfaces_conns)

    return {"ports": ports_conns, "interfaces": interfaces_conns}


def _kpm_connections_to_external(dataflow_data: dict, specification: dict) -> dict:
    """Parse dataflow connections representing external ports/interfaces
    (i.e. connections between IP cores and external metanodes) into 'external'
    section of a Topwrap's design description yaml
    """
    ports_ext_conns = {}
    ifaces_ext_conns = {}
    external = {
        "ports": {"in": [], "out": [], "inout": []},
        "interfaces": {"in": [], "out": []},
    }

    for conn in get_dataflow_external_connections(dataflow_data):
        conn_data = _get_conn_ifaces_and_nodes(conn, dataflow_data)

        # Determine the name of the port/interface
        # to be made external and its node
        if is_external_metanode(conn_data.node_to):
            iface_name = conn_data.iface_from.iface_name
            ip_node, metanode = conn_data.node_from, conn_data.node_to
        elif is_external_metanode(conn_data.node_from):
            iface_name = conn_data.iface_to.iface_name
            ip_node, metanode = conn_data.node_to, conn_data.node_from
        else:
            raise ValueError("Invalid name of external metanode")

        # Determine the direction of external ports/interface
        if metanode["instanceName"] == EXT_OUTPUT_NAME:
            dir = "out"
        elif metanode["instanceName"] == EXT_INPUT_NAME:
            dir = "in"
        else:
            dir = "inout"

        # Get user-defined external name.
        # If none - get internal name as default
        external_name = get_metanode_property_value(metanode)
        if not external_name:
            external_name = iface_name

        if ip_node["name"] == KPMDataflowSubgraphnode.DUMMY_NAME_BASE:
            iface_types = ["port"]
        else:
            # Determine whether we deal with a port or an interface
            spec_inteface = find_spec_interface_by_name(specification, ip_node["name"], iface_name)
            if spec_inteface is None:
                raise ValueError(f"Interface {ip_node['name']} was not found in specification")

            iface_types = spec_inteface["type"]

        if "port" in iface_types:
            ext_conns, ext_section = ports_ext_conns, "ports"
        else:
            ext_conns, ext_section = ifaces_ext_conns, "interfaces"

        # Update 'ports'/'interfaces' and 'external' sections
        if ip_node["instanceName"] not in ext_conns.keys():
            ext_conns[ip_node["instanceName"]] = {}

        if dir != "inout":
            ext_conns[ip_node["instanceName"]][iface_name] = external_name
            if external_name not in external[ext_section][dir]:
                external[ext_section][dir].append(external_name)
        else:
            # don't put inout connections in ext_conns as the rule is to specify them
            # in the "external" section of the YAML
            connection = [ip_node["instanceName"], external_name]
            if connection not in external[ext_section][dir]:
                external[ext_section][dir].append(connection)

    return {"ports": ports_ext_conns, "interfaces": ifaces_ext_conns, "external": external}


def _kpm_connections_to_constant(dataflow_data: dict, specification: dict) -> dict:
    """Parse dataflow connections representing constant ports into design
    'ports' section of a Topwrap's design description yaml
    """
    ports_conns = {"ports": {}}

    for conn in get_dataflow_constant_connections(dataflow_data):
        conn_data = _get_conn_ifaces_and_nodes(conn, dataflow_data)
        ip_node = conn_data.node_to
        const_node = conn_data.node_from

        # Ensure the node is constant metanode
        if not is_constant_metanode(const_node):
            raise ValueError("Invalid name of constant metanode")

        iface_name = conn_data.iface_to.iface_name

        # Constant metanodes have exactly 1 property hence we can take 0th index
        # of the `properties` array of a metanode to access the property
        value = int(const_node["properties"][0]["value"])

        ports_conns["ports"].setdefault(ip_node["instanceName"], {})
        ports_conns["ports"][ip_node["instanceName"]].setdefault(iface_name, value)

    return ports_conns


def _update_ports_ifaces_section(ports_ifaces: dict, externals: dict) -> dict:
    """Helper function to update 'ports' or 'interfaces' section of a design
    description yaml with the collected entries describing external connections
    """
    for ip_name in externals.keys():
        if ip_name not in ports_ifaces.keys():
            ports_ifaces[ip_name] = {}
        ports_ifaces[ip_name].update(externals[ip_name])
    return ports_ifaces


def _kpm_expose_ports(dataflow_json: dict) -> dict:
    exposed_ports = recursive_defaultdict()
    for node in get_all_graph_nodes(dataflow_json):
        for interface in node["interfaces"]:
            if "externalName" in interface.keys():
                exposed_ports[node["instanceName"]][interface["name"]] = interface["externalName"]

    return recursive_defaultdict_to_dict(exposed_ports)


def _kpm_subgraph_ports_definitions(
    dataflow_json: dict, return_recursive_defaultdict: bool = False
) -> dict:
    ports_definitions = recursive_defaultdict()
    directions_shorter = {"input": "in", "output": "out"}
    for node in get_dataflow_subgraph_nodes(dataflow_json):
        for direction in directions_shorter.values():
            ports_definitions[node["instanceName"]]["external"]["ports"][direction] = []

        for interface in node["interfaces"]:
            ports_definitions[node["instanceName"]]["external"]["ports"][
                directions_shorter[interface["direction"]]
            ].append(interface["name"])

    if return_recursive_defaultdict:
        return ports_definitions

    return recursive_defaultdict_to_dict(ports_definitions)


def _add_node_data_to_design(
    topwrap_design: dict, node_instance_name: str, nodes_data: dict, design_field_name: str
):
    """If in "nodes_data" is data about given node then it adds it to "topwrap_design" """
    if node_instance_name in nodes_data.keys():
        topwrap_design[design_field_name][node_instance_name] = nodes_data[node_instance_name]


def _find_necessary_ips_for_hier(
    ips: Dict[str, Dict[Literal["file", "module"], str]],
    design_dict: Dict[str, Any],
    inouts: List[Tuple[str, str]],
):
    keys: Set[str] = set()
    for ip, _ in inouts:
        keys.add(ip)
    for key in (*design_dict["ports"].keys(), *design_dict["interfaces"].keys()):
        keys.add(key)
    return {key: ips[key] for key in keys if key in ips}


def _create_topwrap_design(
    ips: Dict[str, Dict[Literal["file", "module"], str]],
    dataflow_data: dict,
    properties: dict,
    ports: dict,
    interfaces: dict,
    entry_graph_id: str,
    subgraph_ports_external: dict,
    topwrap_design: dict,
) -> dict:
    """Converts the collected data into Topwrap's design description yaml"""
    parent_graph = get_graph_with_id(dataflow_data, entry_graph_id)
    if parent_graph is None:
        raise ValueError(f"Graph with id {entry_graph_id} was not found")

    for node in parent_graph["nodes"]:
        if is_metanode(node):
            continue

        node_instance_name = node["instanceName"]
        _add_node_data_to_design(topwrap_design, node_instance_name, properties, "parameters")
        _add_node_data_to_design(topwrap_design, node_instance_name, interfaces, "interfaces")
        _add_node_data_to_design(topwrap_design, node_instance_name, ports, "ports")

        if "subgraph" in node.keys():
            topwrap_design["hierarchies"][node_instance_name] = subgraph_ports_external[
                node_instance_name
            ]
            design = _create_topwrap_design(
                ips,
                dataflow_data,
                properties,
                ports,
                interfaces,
                node["subgraph"],
                subgraph_ports_external,
                topwrap_design["hierarchies"][node_instance_name]["design"],
            )
            topwrap_design["hierarchies"][node_instance_name]["design"] = design
            ext_ports = subgraph_ports_external[node_instance_name]["external"]["ports"]
            topwrap_design["hierarchies"][node_instance_name]["ips"] = _find_necessary_ips_for_hier(
                ips, design, ext_ports.get("inout", [])
            )

    return topwrap_design


def kpm_dataflow_to_design(dataflow_data: dict, specification: dict) -> DesignDescription:
    """Parse Pipeline Manager dataflow into Topwrap's design description yaml"""
    all_ips = _kpm_nodes_to_ips(dataflow_data, specification)

    properties = _kpm_nodes_to_parameters(dataflow_data)
    ports_ifaces_dict = _kpm_connections_to_ports_ifaces(dataflow_data, specification)
    constants = _kpm_connections_to_constant(dataflow_data, specification)
    externals = _kpm_connections_to_external(dataflow_data, specification)
    node_exposed_ports = _kpm_expose_ports(dataflow_data)
    subgraph_ports_external = _kpm_subgraph_ports_definitions(
        dataflow_data, return_recursive_defaultdict=True
    )

    ports = _update_ports_ifaces_section(ports_ifaces_dict["ports"], externals["ports"])
    ports = _update_ports_ifaces_section(ports_ifaces_dict["ports"], constants["ports"])
    ports = _update_ports_ifaces_section(ports_ifaces_dict["ports"], node_exposed_ports)
    interfaces = _update_ports_ifaces_section(
        ports_ifaces_dict["interfaces"], externals["interfaces"]
    )
    design = _create_topwrap_design(
        all_ips,
        dataflow_data,
        properties,
        ports,
        interfaces,
        dataflow_data.get(
            "entryGraph", dataflow_data["graphs"][0]["id"]
        ),  # if there is no entry graph then there is only one graph in design
        subgraph_ports_external,
        recursive_defaultdict(),
    )

    return DesignDescription.from_dict(
        {
            "ips": _find_necessary_ips_for_hier(
                all_ips, design, externals["external"]["ports"]["inout"]
            ),
            "design": design,
            "external": externals["external"],
        }
    )
