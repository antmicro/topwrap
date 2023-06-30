# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import re
from .kpm_common import *


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


def _kpm_connections_to_ports_ifaces(dataflow_data, specification: dict):
    """ Parse dataflow connections between nodes representing IP cores into
    "ports" and "interfaces" sections of a Topwrap's design description yaml
    """
    ports_conns = {}
    interfaces_conns = {}

    for conn in get_dataflow_ip_connections(dataflow_data):
        [node_from_name, iface_from_name, dir] = find_dataflow_interface_by_id(dataflow_data, conn["from"])
        [node_to_name, iface_to_name, dir] = find_dataflow_interface_by_id(dataflow_data, conn["to"])

        node_to_type = find_dataflow_node_type_by_name(dataflow_data, node_to_name)
        iface_to_type = find_spec_interface_by_name(specification, node_to_type, iface_to_name)["type"]

        if iface_to_type == "port":
            conns_dict = ports_conns
        else:
            conns_dict = interfaces_conns

        if node_to_name not in conns_dict.keys():
             conns_dict[node_to_name] = {}
        conns_dict[node_to_name][iface_to_name] = [node_from_name, iface_from_name]

    return {
        "ports": ports_conns,
        "interfaces": interfaces_conns
    }


def _kpm_connections_to_external(dataflow_data):
    """ Parse dataflow connections representing external ports/interfaces
    (i.e. connections between IP cores and external metanodes) into "external"
    section of a Topwrap's design description yaml
    """
    external = {
        "in": {},
        "out": {},
    }
    # TODO: add "inout" external type

    for conn in get_dataflow_external_connections(dataflow_data):
        [node_to_name, iface_to_name, iface_to_dir] = find_dataflow_interface_by_id(dataflow_data, conn['to'])
        [node_from_name, iface_from_name, iface_from_dir] = find_dataflow_interface_by_id(dataflow_data, conn['from'])
        if node_to_name == EXT_OUTPUT_NAME:
            if node_from_name not in external["out"].keys():
                external["out"][node_from_name] = []
            external["out"][node_from_name].append(iface_from_name)
        elif node_from_name == EXT_INPUT_NAME:
            if node_to_name not in external["in"].keys():
                external["in"][node_to_name] = []
            external["in"][node_to_name].append(iface_to_name)

    return {
        "external": external 
    }


def kpm_dataflow_to_design(dataflow_data, ipcore_to_yamls, specification):
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
