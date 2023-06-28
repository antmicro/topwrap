# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import re
import logging


def _parse_value_width_parameter(param: str) -> dict:
    """ `param` is a string representing a bit vector in Verilog format
    (e.g. "16'h5A5A") which is parsed to a value/width parameter
    """
    quote_pos = param.find("'")
    width = param[:quote_pos]
    radix = param[quote_pos+1]
    value = param[quote_pos+2:]
    radix_to_base = {
        'h': 16,
        'd': 10,
        'o': 8,
        'b': 2
    }

    return {
        'value': int(value, radix_to_base[radix]),
        'width': int(width)
    }


def _maybe_to_int(string: int) -> int | str:
    for base in [10, 16, 2, 8]:
        try:
            return int(string, base)
        except ValueError:
            pass
    return string


def _kpm_properties_to_parameters(properties: dict):
    result = dict()
    for property in properties:
        param_name = property['name']
        param_val = property['value']
        if re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
            param_val = _parse_value_width_parameter(param_val)
        else:
            result[param_name] = _maybe_to_int(param_val)

    return result


def _is_external_metanode(node: dict) -> bool:
    """ Return True if a node is an external metanode, False elsewhere.
    """
    return (node['type'] in ['External Input', 'External Output'])


def _get_ip_nodes(nodes: list) -> list:
    """ Return nodes, which describe some IP cores
    (e.g. filter out external metanodes)
    """
    return [
        node for node in nodes if not _is_external_metanode(node)
    ]


def _kpm_nodes_to_ips(nodes: list, ipcore_to_yamls: dict):
    ips = {
        node['name']: {
            'file': ipcore_to_yamls[node['type']],
            'module': node['type'],
            'parameters': _kpm_properties_to_parameters(node['properties'])
        }
        for node in _get_ip_nodes(nodes)
    }

    return {
        "ips": ips
    }


def _find_spec_interface_by_name(specification: dict, ip_type: str, name: str):
    for node in specification['nodes']:
        if node['type'] != ip_type:
            continue
        for interface in node['interfaces']:
            if interface['name'] == name:
                return interface


def _get_ip_connections(connections: list, nodes: list) -> list:
    """ Return connections between two IP cores
    (e.g. filter out connections to external metanodes)
    """
    ip_connections = []
    ip_ifaces_ids = []
    for ip_node in _get_ip_nodes(nodes):
        for interface in ip_node['interfaces']:
            ip_ifaces_ids.append(interface['id'])

    for conn in connections:
        if conn["from"] in ip_ifaces_ids and conn["to"] in ip_ifaces_ids:
            ip_connections.append(conn)

    return ip_connections 


def _kpm_connections_to_pins(
        connections: list,
        nodes: list,
        specification: dict):

    pins_by_id = {
        "input":  {},
        "output": {}
    }

    for node in nodes:
        # TODO - handle inouts
        for interface in node["interfaces"]:
            iface_name = interface["name"]
            iface_id = interface["id"]
            iface_dir = interface["direction"]
            spec_iface = _find_spec_interface_by_name(
                specification, node['type'],
                iface_name
            )
            if spec_iface is None:
                logging.warning(
                    f'Interface {iface_name}'
                    f'of node {node["type"]} not found in specification'
                )
                continue
            pins_by_id[iface_dir][iface_id] = {
                "ip_name": node['name'],
                "pin_name": iface_name,
                "type": spec_iface['type']
            }

    ports_conns = {}
    interfaces_conns = {}

    for conn in _get_ip_connections(connections, nodes):
        conn_from = pins_by_id["output"][conn["from"]]
        conn_to = pins_by_id["input"][conn["to"]]

        if conn_to["type"] == "port":
            pins_conns = ports_conns
        else:
            pins_conns = interfaces_conns

        if conn_to["ip_name"] not in pins_conns.keys():
            pins_conns[conn_to["ip_name"]] = {}
        pins_conns[conn_to["ip_name"]][conn_to["pin_name"]] = [
            conn_from["ip_name"],
            conn_from["pin_name"]
        ]

    return {
        "ports": ports_conns,
        "interfaces": interfaces_conns
    }


def _get_external_nodes(nodes: list) -> list:
    """ Return metanodes respresenting external inputs and outputs
    """
    return [
        node for node in nodes if _is_external_metanode(node)
    ]


def _get_external_connections(connections: list, nodes: list):
    """ Return connections from/to metanodes representing
    external inputs/outputs
    """
    ip_connections = []
    ext_ifaces_ids = []
    for ip_node in _get_external_nodes(nodes):
        for interface in ip_node['interfaces']:
            ext_ifaces_ids.append(interface['id'])

    for conn in connections:
        if conn["from"] in ext_ifaces_ids or conn["to"] in ext_ifaces_ids:
            ip_connections.append(conn)

    return ip_connections 


def _get_kpm_node_by_interface_id(iface_id: str, nodes: list) -> dict|None:
    for node in nodes:
        for interface in node['interfaces']:
            if iface_id == interface['id']:
                return node


def _get_kpm_interface_name_by_id(iface_id: str, nodes: list) -> str:
    for node in nodes:
        for interface in node['interfaces']:
            if iface_id == interface['id']:
                return interface['name']


def _kpm_connections_to_external(connections: list, nodes: list):
    external = {
        "in": {},
        "out": {},
    }
    # TODO: add "inout" external type

    for conn in _get_external_connections(connections, nodes):
        node_to = _get_kpm_node_by_interface_id(conn["to"], nodes)
        node_from = _get_kpm_node_by_interface_id(conn["from"], nodes)
        if node_to['type'] == 'External Output':
            if node_from["name"] not in external["out"].keys():
                external["out"][node_from["name"]] = []
            external["out"][node_from["name"]].append(_get_kpm_interface_name_by_id(conn["from"], nodes))
        elif node_from['type'] == 'External Input':
            if node_to["name"] not in external["in"].keys():
                external["in"][node_to["name"]] = []
            external["in"][node_to["name"]].append(_get_kpm_interface_name_by_id(conn["to"], nodes))

    return {
        "external": external 
    }


def kpm_dataflow_to_design(data, ipcore_to_yamls, specification):
    ips = _kpm_nodes_to_ips(data["graph"]["nodes"], ipcore_to_yamls)
    pins = _kpm_connections_to_pins(
        data["graph"]["connections"],
        data["graph"]["nodes"],
        specification
    )
    external = _kpm_connections_to_external(data["graph"]["connections"], data["graph"]["nodes"])

    return {
        **ips,
        **pins,
        **external
    }
