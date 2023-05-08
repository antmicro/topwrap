# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import re


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


def _kpm_options_to_parameters(options: list):
    result = dict()
    for option in options:
        param_name = option[0]
        param_val = option[1]
        if re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
            param_val = _parse_value_width_parameter(param_val)
        result[param_name] = _maybe_to_int(param_val)

    return result


def _kpm_nodes_to_ips(nodes: list, ipcore_to_yamls: dict):
    ips = {
        node['name']: {
            'file': ipcore_to_yamls[node['type']],
            'module': node['type'],
            'parameters': _kpm_options_to_parameters(node['options'])
        }
        for node in nodes
    }

    return {
        "ips": ips
    }


def _kpm_connections_to_pins(connections: list, nodes: list):
    pins_by_id = {
        "inputs":  {},
        "outputs": {}
    }

    for node in nodes:
        for iface in node['interfaces']:
            # TODO - handle inouts
            if iface[1]['isInput'] is True:
                dir = "inputs"
            else:
                dir = "outputs"

            pins_by_id[dir][iface[1]['id']] = {
                "ip_name": node['name'],
                "pin_name": iface[0],
                "type": iface[1]['type']
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


def kpm_dataflow_to_design(data, ipcore_to_yamls):
    ips = _kpm_nodes_to_ips(data["nodes"], ipcore_to_yamls)
    pins = _kpm_connections_to_pins(data["connections"], data["nodes"])

    return {
        **ips,
        **pins
    }
