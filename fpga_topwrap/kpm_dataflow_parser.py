# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import re
from .kpm_common import (
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    EXT_INOUT_NAME,
    get_dataflow_ip_nodes,
    get_dataflow_ip_connections,
    find_dataflow_interface_by_id,
    find_dataflow_node_type_by_name,
    find_spec_interface_by_name,
    get_dataflow_external_connections,
    get_metanode_property_value,
    find_dataflow_node_by_interface_id
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
    return {
        node['name']: {
            'file': ipcore_to_yamls[node['type']],
            'module': node['type'],
            'parameters': _kpm_properties_to_parameters(node['properties'])
        }
        for node in get_dataflow_ip_nodes(dataflow_data)
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


def _kpm_connections_to_external(dataflow_data, specification) -> dict:
    """ Parse dataflow connections representing external ports/interfaces
    (i.e. connections between IP cores and external metanodes) into "external"
    section of a Topwrap's design description yaml
    """
    ports_ext_conns = {}
    ifaces_ext_conns = {}
    external = {
        "ports": {
            "in": [],
            "out": [],
            "inout": []
        },
        "interfaces": {
            "in": [],
            "out": [],
            "inout": []
        }
    }

    for conn in get_dataflow_external_connections(dataflow_data):
        iface_to = find_dataflow_interface_by_id(
            dataflow_data, conn['to'])
        iface_from = find_dataflow_interface_by_id(
            dataflow_data, conn['from'])
        node_to = find_dataflow_node_by_interface_id(
            dataflow_data, conn['to'])
        node_from = find_dataflow_node_by_interface_id(
            dataflow_data, conn['from'])

        # Determine the name of the port/interface
        # to be made external and its node
        if node_to['name'] in [EXT_OUTPUT_NAME, EXT_INOUT_NAME]:
            dir = 'out' if node_to['name'] == EXT_OUTPUT_NAME else 'inout'
            iface_name = iface_from['iface_name']
            ip_node, metanode = node_from, node_to
        elif node_from['name'] in [EXT_INPUT_NAME, EXT_INOUT_NAME]:
            dir = 'in' if node_from['name'] == EXT_INPUT_NAME else 'inout'
            iface_name = iface_to['iface_name']
            ip_node, metanode = node_to, node_from
        else:
            raise ValueError("Invalid name of external metanode")

        # Get user-defined external name.
        # If none - get internal name as default
        external_name = get_metanode_property_value(metanode)
        if not external_name:
            external_name = iface_name

        # Determine whether we deal with a port or an interface
        iface_type = find_spec_interface_by_name(
            specification, ip_node["type"], iface_name
        )["type"]
        if iface_type in ['port', 'port_inout']:
            ext_conns, ext_section = ports_ext_conns, 'ports'
        else:
            ext_conns, ext_section = ifaces_ext_conns, 'interfaces'

        # Update 'ports'/'interfaces' and 'external' sections
        if ip_node['name'] not in ext_conns.keys():
            ext_conns[ip_node['name']] = {}
        ext_conns[ip_node['name']][iface_name] = external_name
        if external_name not in external[ext_section][dir]:
            external[ext_section][dir].append(external_name)

    return {
        "ports": ports_ext_conns,
        "interfaces": ifaces_ext_conns,
        "external": external
    }


def _update_ports_ifaces_section(ports_ifaces: dict, externals: dict) -> dict:
    """ Helper function to update 'ports' or 'interfaces' section of a design
    description yaml with the collected entries describing external connections
    """
    for ip_name in externals.keys():
        if ip_name not in ports_ifaces.keys():
            ports_ifaces[ip_name] = {}
        ports_ifaces[ip_name].update(externals[ip_name])
    return ports_ifaces


def kpm_dataflow_to_design(
        dataflow_data,
        ipcore_to_yamls: dict, specification) -> dict:
    """ Parse Pipeline Manager dataflow into Topwrap's design description yaml
    """
    ips = _kpm_nodes_to_ips(dataflow_data, ipcore_to_yamls)
    ports_ifaces_dict = _kpm_connections_to_ports_ifaces(
        dataflow_data, specification)
    externals = _kpm_connections_to_external(dataflow_data, specification)

    ports = _update_ports_ifaces_section(
        ports_ifaces_dict['ports'], externals['ports'])
    interfaces = _update_ports_ifaces_section(
        ports_ifaces_dict['interfaces'], externals['interfaces'])

    return {
        'ips': ips,
        'ports': ports,
        'interfaces': interfaces,
        'external': externals['external']
    }
