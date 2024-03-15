# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from itertools import cycle

from .kpm_common import EXT_INOUT_NAME, EXT_INPUT_NAME, EXT_OUTPUT_NAME
from .parsers import parse_port_map


def _ipcore_param_to_kpm_value(param) -> str:
    """Returns a parameter default value, that will be displayed
    as an option in Pipeline Manager Node.

    :param param: may be int, str or {'value': ..., 'width': ... } dict.
    :return: in the dict case, the parameter will be shown in a Verilog
        hex format - e.g. {'value': 40, 'width': 16 } will be displayed
        as 16'h0028
    """
    if isinstance(param, str):
        return param
    elif isinstance(param, int):
        return str(param)
    elif isinstance(param, dict) and param.keys() == {"value", "width"}:
        width = str(param["width"])
        value = hex(param["value"])[2:]
        return width + "'h" + value


def _ipcore_params_to_kpm(params: dict) -> list:
    """Returns a list of parameters in a format used in KPM specification

    :param params: a dict containing parameter names and their values,
        gathered from IP core description YAML

    :return: a list of KPM specification 'properties', which correspond to
        given IP core parameters
    """
    return [
        {"name": param[0], "type": "text", "default": _ipcore_param_to_kpm_value(param[1])}
        for param in params.items()
    ]


def _ipcore_ports_to_kpm(ports: dict) -> list:
    """Returns lists of ports grouped by direction (inputs/outputs)
    in a format used in KPM specification.

    :param ports: a dict containing ports descriptions,
        gathered from IP core description YAML

    :return: a dict containing KPM "interfaces", which
        correspond to given IP core ports
    """
    inputs = [
        {
            # In ip core yamls each port is described as a separate,
            # one-element list. Here `port` is a one-element list containing a
            # single string (i.e. port name), which is accessed with `port[0]`
            "name": port[0],
            "type": ["port"],
            "direction": "input",
        }
        for port in ports["in"]
    ]
    outputs = [{"name": port[0], "type": ["port"], "direction": "output"} for port in ports["out"]]
    inouts = [
        {"name": port[0], "type": ["port"], "direction": "inout", "side": "right"}
        for port in ports["inout"]
    ]

    return inputs + outputs + inouts


def _ipcore_ifaces_to_kpm(ifaces: dict):
    """Returns a list of interfaces grouped by direction (inputs/outputs)
    in a format used in KPM specification. Master interfaces are considered
    outputs and slave interfaces are considered inputs.

    :param ifaces: a dict containing interfaces descriptions,
        gathered from IP core description YAML

    :return: a dict containing KPM "inputs" and "outputs", which
        correspond to given IP core interfaces
    """
    inputs = [
        {
            "name": iface,
            "type": [f'iface_{ifaces[iface]["interface"]}'],
            "direction": "input",
        }
        for iface in ifaces.keys()
        if ifaces[iface]["mode"] == "slave"
    ]
    outputs = [
        {
            "name": iface,
            "type": [f'iface_{ifaces[iface]["interface"]}'],
            "direction": "output",
            "maxConnectionsCount": 1,
        }
        for iface in ifaces.keys()
        if ifaces[iface]["mode"] == "master"
    ]

    return inputs + outputs


def _ipcore_to_kpm(yamlfile: str) -> dict:
    """Returns a single KPM specification 'node' representing
    given IP core description YAML file.

    :param yamlfile: IP core description file to be converted

    :return: a dict representing single KPM specification 'node'
    """
    ip_yaml = parse_port_map(yamlfile)

    ip_name = os.path.splitext(os.path.basename(yamlfile))[0]
    kpm_params = _ipcore_params_to_kpm(ip_yaml["parameters"])
    kpm_ports = _ipcore_ports_to_kpm(ip_yaml["signals"])
    kpm_ifaces = _ipcore_ifaces_to_kpm(ip_yaml["interfaces"])

    return {
        "name": ip_name,
        "layer": ip_name,
        "category": "IPcore",
        "properties": kpm_params,
        "interfaces": kpm_ports + kpm_ifaces,
        "additionalData": yamlfile,
    }


def _duplicate_ipcore_types_check(specification: str):
    # check for duplicate IP core types
    types_set = set()
    duplicates = set()
    for node in specification["nodes"]:
        if node["layer"] in types_set:
            duplicates.add(node["layer"])
        else:
            types_set.add(node["layer"])
    for dup in list(duplicates):
        logging.warning(f"Multiple IP cores of type '{dup}'")


def _generate_external_metanode(direction: str, interfaces_types: list) -> dict:
    """Generate a dict representing external metanode.

    :param direction: a string describing the direction of a metanode ("inout"/"output"/"input")
    :param interfaces_types: list of all the interfaces types occurring in nodes representing
    IP cores. These are necessary to append to "layer" property of the interface of the node, so
    that it is possible to connect any interface to external metanode.

    :return: a dict representing an external metanode
    """
    if direction == "input":
        name = EXT_INPUT_NAME
        iface_dir = "output"
    elif direction == "output":
        name = EXT_OUTPUT_NAME
        iface_dir = "input"
    elif direction == "inout":
        name = EXT_INOUT_NAME
        iface_dir = "inout"
    else:
        raise ValueError(f"Unknown direction: {direction}")

    metanode = {
        "name": name,
        "layer": name,
        "category": "Metanode",
        "properties": [{"name": "External Name", "type": "text", "default": ""}],
        "interfaces": [
            {"name": "external", "type": ["port"] + interfaces_types, "direction": iface_dir}
        ],
    }

    return metanode


def _generate_ifaces_styling(interfaces_types: list) -> dict:
    """Generate the `spec["metadata"]["interfaces"]` part of the KPM specification, which is
    responsible for styling interfaces and their connections.

    :param interfaces_types: a list of interfaces types, e.g. ["iface_AXI4", "iface_AXILite"]

    :return: a dict of type {"iface_type1":  {...}, "iface_type2":  {...}, ...}, which describes
    styling of all the interfaces
    """
    COLOR_WHITE = "#ffffff"
    COLOR_GREEN = "#00ca7c"

    ports_styling = {
        "port": {
            "interfaceColor": COLOR_GREEN,
            "interfaceConnectionColor": COLOR_WHITE,
            "interfaceConnectionPattern": "solid",
        },
    }
    interfaces_styling = {
        iface_type: {
            "interfaceColor": COLOR_GREEN,
            "interfaceConnectionColor": COLOR_WHITE,
            "interfaceConnectionPattern": "dashed",
        }
        for iface_type in interfaces_types
    }

    return {**ports_styling, **interfaces_styling}


def _get_ifaces_types(specification: dict) -> list:
    """Return a list of all interfaces types from specification that are interfaces types."""
    return list(
        set(
            [
                iface_type
                for node in specification["nodes"]
                for iface in node["interfaces"]
                for iface_type in iface["type"]
                if iface_type != "port"
            ]
        )
    )


def ipcore_yamls_to_kpm_spec(yamlfiles: list) -> dict:
    """Translate Topwrap's IP core description YAMLs into
    KPM specification 'nodes'.

    :param yamlfiles: IP core description YAMLs, that will be converted
    into KPM specification 'nodes'

    :return: a dict containing KPM specification in which each 'node'
        represents a separate IP core
    """
    specification = {
        "version": "20230830.11",
        "metadata": {
            "allowLoopbacks": True,
            "connectionStyle": "orthogonal",
            "movementStep": 15,
            "backgroundSize": 15,
            "layout": "CytoscapeEngine - grid",
            "twoColumn": True,
        },
        "nodes": [_ipcore_to_kpm(yamlfile) for yamlfile in yamlfiles],
    }

    interfaces_types = _get_ifaces_types(specification)
    specification["nodes"] += [
        _generate_external_metanode("input", interfaces_types),
        _generate_external_metanode("output", interfaces_types),
        _generate_external_metanode("inout", interfaces_types),
    ]
    specification["metadata"]["interfaces"] = _generate_ifaces_styling(interfaces_types)

    _duplicate_ipcore_types_check(specification)

    return specification
