# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import re
from .kpm_common import (
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    get_dataflow_ip_nodes,
    get_dataflow_ip_connections,
    find_dataflow_interface_by_id,
    find_dataflow_node_type_by_name,
    find_spec_interface_by_name,
    get_dataflow_external_connections
)


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


def _maybe_to_int(string: int):
    for base in [10, 16, 2, 8]:
        try:
            return int(string, base)
        except ValueError:
            pass
    return string


def _kpm_properties_to_parameters(properties: dict) -> dict:
    """ Parse `properties` taken from a dataflow node into
    Topwrap's IP core's parameters.
    """
    result = dict()
    for property in properties:
        param_name = property['name']
        param_val = property['value']
        if re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
            result[param_name] = _parse_value_width_parameter(param_val)
        else:
            result[param_name] = _maybe_to_int(param_val)
    return result


def _kpm_nodes_to_ips(dataflow_data, ipcore_to_yamls: dict) -> dict:
    """ Parse dataflow nodes into Topwrap's "ips" section
    of a design description yaml
    """
    ips = {
        node['name']: {
            'file': ipcore_to_yamls[node['type']],
            'module': node['type'],
            'parameters': _kpm_properties_to_parameters(node['properties'])
        }
        for node in get_dataflow_ip_nodes(dataflow_data)
    }

    return {
        "ips": ips
    }


def _kpm_connections_to_ports_ifaces(
        dataflow_data,
        specification: dict) -> dict:
    """ Parse dataflow connections between nodes representing IP cores into
    "ports" and "interfaces" sections of a Topwrap's design description yaml
    """
    ports_conns = {}
    interfaces_conns = {}

    for conn in get_dataflow_ip_connections(dataflow_data):
        iface_from = find_dataflow_interface_by_id(dataflow_data, conn["from"])
        iface_to = find_dataflow_interface_by_id(dataflow_data, conn["to"])

        node_to_type = find_dataflow_node_type_by_name(
            dataflow_data, iface_to["node_name"]
        )
        iface_to_type = find_spec_interface_by_name(
            specification, node_to_type, iface_to["iface_name"]
        )["type"]

        if iface_to_type in ["port", "port_inout"]:
            conns_dict = ports_conns
        else:
            conns_dict = interfaces_conns

        if iface_to["node_name"] not in conns_dict.keys():
            conns_dict[iface_to["node_name"]] = {}
        conns_dict[iface_to["node_name"]][iface_to["iface_name"]] = [
            iface_from["node_name"], iface_from["iface_name"]
        ]

    return {
        "ports": ports_conns,
        "interfaces": interfaces_conns
    }


def _kpm_connections_to_external(dataflow_data) -> dict:
    """ Parse dataflow connections representing external ports/interfaces
    (i.e. connections between IP cores and external metanodes) into "external"
    section of a Topwrap's design description yaml
    """
    external = {
        "in": {},
        "out": {},
        "inout": {}
    }

    for conn in get_dataflow_external_connections(dataflow_data):
        iface_to = find_dataflow_interface_by_id(dataflow_data, conn['to'])
        iface_from = find_dataflow_interface_by_id(
            dataflow_data, conn['from']
        )

        if iface_to["node_name"] == EXT_OUTPUT_NAME:
            if iface_from["iface_dir"] == "output":
                if iface_from["node_name"] not in external["out"].keys():
                    external["out"][iface_from["node_name"]] = []
                external["out"][iface_from["node_name"]].append(
                    iface_from["iface_name"]
                )
            elif iface_from["iface_dir"] == "inout":
                if iface_from["node_name"] not in external["inout"].keys():
                    external["inout"][iface_from["node_name"]] = []
                external["inout"][iface_from["node_name"]].append(
                    iface_from["iface_name"]
                )
        elif iface_from["node_name"] == EXT_INPUT_NAME:
            if iface_to["node_name"] not in external["in"].keys():
                external["in"][iface_to["node_name"]] = []
            external["in"][iface_to["node_name"]].append(
                iface_to["iface_name"]
            )

    return {
        "external": external
    }


def kpm_dataflow_to_design(
        dataflow_data,
        ipcore_to_yamls: dict, specification) -> dict:
    """ Parse Pipeline Manager dataflow into Topwrap's design description yaml
    """
    ips = _kpm_nodes_to_ips(dataflow_data, ipcore_to_yamls)
    pins = _kpm_connections_to_ports_ifaces(dataflow_data, specification)
    external = _kpm_connections_to_external(dataflow_data)

    return {
        **ips,
        **pins,
        **external
    }