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


def _maybe_to_int(string: int) -> int|str:
    for base in [10, 16, 2, 8]:
        try:
            return int(string, base)
        except ValueError:
            pass
    return string


def _kpm_properties_to_parameters(properties: dict):
    result = dict()
    for param_name in properties.keys():
        param_val = properties[param_name]['value']
        if re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
            param_val = _parse_value_width_parameter(param_val)
        result[param_name] = _maybe_to_int(param_val)

    return result


def _kpm_nodes_to_ips(nodes: list, ipcore_to_yamls: dict):
    ips = {
        node['name']: {
            'file': ipcore_to_yamls[node['type']],
            'module': node['type'],
            'parameters': _kpm_properties_to_parameters(node['properties'])
        }
        for node in nodes
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


def _kpm_connections_to_pins(connections: list, nodes: list, specification: dict):
    pins_by_id = {
        "inputs":  {},
        "outputs": {}
    }

    for node in nodes:
        # TODO - handle inouts
        for dir in ['inputs', 'outputs']:
            for iface_name in node[dir].keys():
                spec_iface = _find_spec_interface_by_name(specification, node['type'], iface_name)
                if spec_iface is None:
                    logging.warning(
                        f'Interface {iface_name} of node {node["type"]} not found in specification')
                    continue
                iface_id = node[dir][iface_name]['id']
                pins_by_id[dir][iface_id] = {
                    "ip_name": node['name'],
                    "pin_name": iface_name,
                    "type": spec_iface['type']
                }

    ports_conns = {}
    interfaces_conns = {}

    for conn in connections:
        conn_from = pins_by_id["outputs"][conn["from"]]
        conn_to = pins_by_id["inputs"][conn["to"]]

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

    # TODO - handle external ports
    return {
        "ports": ports_conns,
        "interfaces": interfaces_conns
    }


def kpm_dataflow_to_design(data, ipcore_to_yamls, specification):
    ips = _kpm_nodes_to_ips(data["graph"]["nodes"], ipcore_to_yamls)
    pins = _kpm_connections_to_pins(
        data["graph"]["connections"], 
        data["graph"]["nodes"], 
        specification
    )

    return {
        **ips,
        **pins
    }
