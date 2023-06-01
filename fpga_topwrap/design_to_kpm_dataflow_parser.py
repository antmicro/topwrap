# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import List
from time import time
from yaml import safe_load


class IDGenerator(object):
    """ ID generator implementation just as in BaklavaJS
    """
    __counter = 0

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(IDGenerator, cls).__new__(cls)
        return cls.instance

    def generate_id(self) -> str:
        result = str(int(time() * 1000)) + str(IDGenerator.__counter)
        IDGenerator.__counter += 1
        return result


class KPMDataflowNodeInterface:
    def __init__(self, name: str):
        generator = IDGenerator()
        self.id = "ni_" + generator.generate_id()
        self.name = name


class KPMDataflowNodeProperty:
    def __init__(self, name: str, value: str):
        generator = IDGenerator()
        self.id = generator.generate_id()
        self.name = name
        self.value = value


class KPMDataflowNode:
    __default_width = 200

    def __init__(self,
                 name: str,
                 type: str,
                 properties: List[KPMDataflowNodeProperty],
                 inputs: List[KPMDataflowNodeInterface],
                 outputs: List[KPMDataflowNodeInterface]) -> None:

        generator = IDGenerator()
        self.id = "node_" + generator.generate_id()
        self.name = name
        self.type = type
        self.properties = properties
        self.inputs = inputs
        self.outputs = outputs

    def to_json_format(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "inputs": {
                input.name: {
                    "id": input.id
                } 
                for input in self.inputs
            },
            "outputs": {
                output.name: {
                    "id": output.id
                } 
                for output in self.outputs
            },
            "position": {
                "x": 0,
                "y": 0
            },
            "width": KPMDataflowNode.__default_width,
            "twoColumn": False,
            "properties": {
                property.name: {
                    "id": property.id,
                    "value": property.value
                }
                for property in self.properties
            }
        }


class KPMDataflowConnection:
    def __init__(self, id_from: str, id_to: str) -> None:
        generator = IDGenerator()
        self.id = generator.generate_id()
        self.id_from = id_from
        self.id_to = id_to

    def to_json_format(self) -> dict:
        return {
            "id": self.id,
            "from": self.id_from,
            "to": self.id_to
        }


def _get_specification_node_by_type(type: str, specification: dict) -> dict:
    for node in specification['nodes']:
        if type == node['type']:
            return node
    logging.warning(f'Node type "{type}" not found in specification')


def _ipcore_param_to_kpm_value(param) -> str:
    if isinstance(param, str):
        return param
    elif isinstance(param, int):
        return str(param)
    elif isinstance(param, dict) and param.keys() == {'value', 'width'}:
        width = str(param['width'])
        value = hex(param['value'])[2:]
        return width + "\'h" + value


def kpm_nodes_from_design_descr(
        design_descr: dict,
        specification: dict) -> List[KPMDataflowNode]:
    """ Generate KPM dataflow nodes based on Topwrap's design
    description yaml (e.g. generated from YAML design description)
    and already loaded KPM specification.
    """
    ips = design_descr['ips']
    nodes = []

    for ip_name in ips.keys():
        ip = ips[ip_name]
        ip_type = os.path.splitext(os.path.basename(ip['file']))[0]
        spec_node = _get_specification_node_by_type(ip_type, specification)
        if spec_node is None:
            continue

        properties = {
            prop['name']: KPMDataflowNodeProperty(prop['name'], prop['default']) 
            for prop in spec_node['properties']
        }
        if 'parameters' in ip.keys():
            for (param_name, param_val) in ip['parameters'].items():
                if param_name in properties.keys():
                    properties[param_name].value = _ipcore_param_to_kpm_value(param_val) # noqa
                else:
                    logging.warning(f"Parameter '{param_name}' not found in node {ip_name}")

        inputs = [KPMDataflowNodeInterface(
            input['name']) for input in spec_node['interfaces'] if input['direction'] == 'input'] # noqa
        outputs = [KPMDataflowNodeInterface(
            output['name']) for output in spec_node['interfaces'] if output['direction'] == 'output'] # noqa

        nodes.append(KPMDataflowNode(ip_name, ip_type, list(properties.values()), inputs, outputs)) # noqa
    return nodes


def _get_dataflow_interface_by_name(name: str, node_name: str, nodes: List[KPMDataflowNode]) -> KPMDataflowNodeInterface:
    """ Find `name` interface of a node (representing an IP core) named `node_name`. 
    """
    for node in nodes:
        if node.name == node_name:
            for iface in node.inputs + node.outputs:
                if iface.name == name:
                    return iface
            logging.warning(f"Interface '{name}' not found in node {node_name}")
            return
    logging.warning(f"Node '{node_name}' not found")


def _create_kpm_dataflow_connection(
        name_from: str,
        ip_from: str,
        name_to: str,
        ip_to: str,
        nodes: List[KPMDataflowNode]) -> KPMDataflowConnection:

    """ Create a KPMDataflowConnection between 2 interfaces of 2 nodes represeting IP cores
    """    
    kpm_iface_from = _get_dataflow_interface_by_name(name_from, ip_from, nodes)
    kpm_iface_to = _get_dataflow_interface_by_name(name_to, ip_to, nodes)
    if kpm_iface_from is None or kpm_iface_to is None:
        return None
    return KPMDataflowConnection(kpm_iface_from.id, kpm_iface_to.id)


def _parse_design_descr_connections(conns_dict: dict, nodes: List[KPMDataflowNode]) -> List[KPMDataflowConnection]:
    """ Helper function for parsing "ports" or "interfaces" section of
    a design description yaml into a list of KPMDataflowConnection
    """
    connections = []
    for ip_conns in conns_dict.items():
        to_ip_name = ip_conns[0]
        for conn in ip_conns[1].items():
            to_port_name = conn[0]
            if not isinstance(conn[1], list):
                # TODO - handle case where port has a default value
                # instead of being connected with another port
                continue
            from_ip_name = conn[1][0]
            from_port_name = conn[1][1]
            connection = _create_kpm_dataflow_connection(from_port_name, from_ip_name, to_port_name, to_ip_name, nodes)
            if connection is not None:
                connections.append(connection)
    return connections


def kpm_connections_from_design_descr(
        design_descr: dict,
        nodes: List[KPMDataflowNode]) -> List[KPMDataflowConnection]:

    """ Generate KPM connections based on the data from `design_descr`.
    We also need a list of previously generated KPM dataflow nodes, because the
    connections in KPM are specified using id's of their interfaces
    """
    port_conns = {}
    if 'ports' in design_descr.keys():
        port_conns = design_descr['ports']
    interface_conns = {}
    if 'interfaces' in design_descr.keys():
        interface_conns = design_descr['interfaces']

    return _parse_design_descr_connections(port_conns, nodes) + _parse_design_descr_connections(interface_conns, nodes)


def kpm_dataflow_from_design_descr(
        design_descr: dict,
        specification: dict) -> dict:

    nodes = kpm_nodes_from_design_descr(design_descr, specification)
    connections = kpm_connections_from_design_descr(design_descr, nodes)
    generator = IDGenerator()
    return {
        "graph": {
            "id": generator.generate_id(),
            "nodes": [
                node.to_json_format() for node in nodes
            ],
            "connections": [
                connection.to_json_format() for connection in connections
            ],
            "inputs": [],
            "outputs": []
        },
        "graphTemplates": []
    }
