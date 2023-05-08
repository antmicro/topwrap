# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from .parsers import parse_port_map


def _ipcore_param_to_kpm_value(param) -> str:
    """ Returns a parameter default value, that will be displayed
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
    elif isinstance(param, dict) and param.keys() == {'value', 'width'}:
        width = str(param['width'])
        value = hex(param['value'])[2:]
        return width + "\'h" + value


def _ipcore_params_to_kpm(params: dict) -> list:
    """ Returns a list of parameters in a format used in KPM specification

    :param params: a dict containing parameter names and their values,
        gathered from IP core description YAML

    :return: a list of KPM specification 'properties', which correspond to
        given IP core parameters
    """
    return [
        {
            'name': param[0],
            'type': 'text',
            'default': _ipcore_param_to_kpm_value(param[1])
        }
        for param in params.items()
    ]


def _ipcore_ports_to_kpm(ports: dict) -> dict:
    """ Returns lists of ports grouped by direction (inputs/outputs)
    in a format used in KPM specification.

    :param ports: a dict containing ports descriptions,
        gathered from IP core description YAML

    :return: a dict containing KPM "inputs" and "outputs", which
        correspond to given IP core ports
    """
    inputs = [
        {
            'name': port[0],
            'type': 'port'
        }
        for port in ports['in']
    ]
    outputs = [
        {
            'name': port[0],
            'type': 'port'
        }
        for port in ports['out']
    ]
    # TODO - inouts are not supported in KPM for now

    return {
        "inputs": inputs,
        "outputs": outputs,
    }


def _ipcore_ifaces_to_kpm(ifaces: dict):
    """ Returns a list of interfaces grouped by direction (inputs/outputs)
    in a format used in KPM specification. Master interfaces are considered
    outputs and slave interfaces are considered inputs.

    :param ifaces: a dict containing interfaces descriptions,
        gathered from IP core description YAML

    :return: a dict containing KPM "inputs" and "outputs", which
        correspond to given IP core interfaces
    """
    inputs = [
        {
            'name': iface,
            'type': 'iface_' + ifaces[iface]['interface']
        }
        for iface in ifaces.keys() if ifaces[iface]['mode'] == 'slave'
    ]
    outputs = [
        {
            'name': iface,
            'type': 'iface_' + ifaces[iface]['interface']
        }
        for iface in ifaces.keys() if ifaces[iface]['mode'] == 'master'
    ]

    return {
        "inputs": inputs,
        "outputs": outputs,
    }


def _ipcore_to_kpm(yamlfile: str) -> dict:
    """ Returns a single KPM specification 'node' representing
    given IP core description YAML file.

    :param yamlfile: IP core description file to be converted

    :return: a dict representing single KPM specification 'node'
    """
    ip_yaml = parse_port_map(yamlfile)

    ip_name = os.path.splitext(os.path.basename(yamlfile))[0]
    kpm_params = _ipcore_params_to_kpm(ip_yaml['parameters'])
    kpm_ports = _ipcore_ports_to_kpm(ip_yaml['signals'])
    kpm_ifaces = _ipcore_ifaces_to_kpm(ip_yaml['interfaces'])

    return {
        'name': ip_name,
        'type': ip_name,
        'category': 'IPcore',
        'properties': kpm_params,
        'inputs': kpm_ports['inputs'] + kpm_ifaces['inputs'],
        'outputs': kpm_ports['outputs'] + kpm_ifaces['outputs']
    }


def _duplicate_ipcore_types_check(specification: str):
    # check for duplicate IP core types
    types_set = set()
    duplicates = set()
    for node in specification["nodes"]:
        if node['type'] in types_set:
            duplicates.add(node['type'])
        else:
            types_set.add(node['type'])
    for dup in list(duplicates):
        logging.warning(f"Multiple IP cores of type '{dup}'")


def ipcore_yamls_to_kpm_spec(yamlfiles: list) -> dict:
    """ Translate Topwrap's IP core description YAMLs into
    KPM specification 'nodes'.

    :param yamlfiles: IP core desciption YAMLs, that will be converted
    into KPM specification 'nodes'

    :return: a dict contatining KPM specification in which each 'node'
        represents a separate IP core
    """
    specification = {
        "metadata": {
            "allowLoopbacks": True,
            "connectionStyle": "orthogonal"
        },
        "nodes": [
            _ipcore_to_kpm(yamlfile)
            for yamlfile in yamlfiles
        ]
    }

    _duplicate_ipcore_types_check(specification)

    return specification
