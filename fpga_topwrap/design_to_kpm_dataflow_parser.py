# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import List
from time import time
from yaml import safe_load
from .design_description import \
    DesignDescription, DesignIP, Direction, \
    Interface, InterfaceConnection, Port, PortConnection
from enum import Enum


def design_descr_from_yaml(yamlcontent: str) -> DesignDescription:
    """ Parse design description YAML file into DesignDescription
    """
    design = safe_load(yamlcontent)

    yaml_ips = design['ips'] if 'ips' in design.keys() else {}
    yaml_ports = design['ports'] if 'ports' in design.keys() else {}
    yaml_ifaces = design['interfaces'] if 'interfaces' in design.keys() else {}
    yaml_external = design['external'] if 'external' in design.keys() else {}

    design_ips = []
    ports_conns = []
    interfaces_conns = []
    external = []

    for ip_name in yaml_ips.keys():
        descr_file = yaml_ips[ip_name]['file']
        module = os.path.splitext(os.path.basename(descr_file))[0]
        if 'parameters' in yaml_ips[ip_name].keys():
            parameters = yaml_ips[ip_name]['parameters']
        else:
            parameters = {}
        design_ips.append(DesignIP(ip_name, descr_file, module, parameters))

    for ip_name in yaml_ports.keys():
        for port_name in yaml_ports[ip_name].keys():
            port_to = Port(port_name, ip_name, Direction.IN)
            value = yaml_ports[ip_name][port_name]
            if isinstance(value, int):
                ports_conns.append(PortConnection(None, port_to, value))
            elif isinstance(value, list):
                port_from = Port(value[1], value[0], Direction.OUT)
                ports_conns.append(PortConnection(port_from, port_to))

    for ip_name in yaml_ifaces.keys():
        for iface_name in yaml_ifaces[ip_name].keys():
            iface_to = Interface(iface_name, ip_name, Direction.IN, None)
            value = yaml_ifaces[ip_name][iface_name]
            iface_from = Interface(value[1], value[0], Direction.OUT, None)
            interfaces_conns.append(InterfaceConnection(iface_from, iface_to))

    for ip_name in yaml_external.keys():
        pass  # TODO - find a way to get external port directions

    return DesignDescription(design_ips, ports_conns, interfaces_conns, external) # noqa


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
        design_descr: DesignDescription,
        specification: dict) -> List[KPMDataflowNode]:
    """ Generate KPM dataflow nodes based on Topwrap's abstract
    DesignDescription object (e.g. generated from YAML design description)
    and already loaded KPM specification.
    """
    nodes = []
    for ip in design_descr.ips:
        spec_node = _get_specification_node_by_type(ip.module, specification)
        if spec_node is None:
            continue

        properties = [KPMDataflowNodeProperty(
            prop['name'], prop['default']) for prop in spec_node['properties']]
        for property in properties:  # override default values
            if property.name in ip.parameters.keys():
                property.value = _ipcore_param_to_kpm_value(ip.parameters[property.name]) # noqa

        inputs = [KPMDataflowNodeInterface(
            input['name']) for input in spec_node['interfaces'] if input['direction'] == 'input'] # noqa
        outputs = [KPMDataflowNodeInterface(
            output['name']) for output in spec_node['interfaces'] if output['direction'] == 'output'] # noqa

        nodes.append(KPMDataflowNode(ip.name, ip.module, properties, inputs, outputs))
    return nodes


def _get_dataflow_node_by_name(
        name: str,
        nodes: List[KPMDataflowNode]) -> KPMDataflowNode:

    for node in nodes:
        if node.name == name:
            return node
    logging.warning(f"Node '{name}' not found in the design")


def _get_dataflow_interface_by_name(
        name: str,
        node: KPMDataflowNode) -> KPMDataflowNodeInterface:

    for interface in node.inputs + node.outputs:
        if interface.name == name:
            return interface
    logging.warning(f"Interface '{name}' not found in node {node.name}")


def _create_kpm_dataflow_connection(
        name_from: str,
        ip_from: str,
        name_to: str,
        ip_to: str,
        nodes: List[KPMDataflowNode]) -> KPMDataflowConnection:

    node_from = _get_dataflow_node_by_name(ip_from, nodes)
    node_to = _get_dataflow_node_by_name(ip_to, nodes)
    if node_from is None or node_to is None:
        return None
    kpm_iface_from = _get_dataflow_interface_by_name(name_from, node_from)
    kpm_iface_to = _get_dataflow_interface_by_name(name_to, node_to)
    if kpm_iface_from is None or kpm_iface_to is None:
        return None
    return KPMDataflowConnection(kpm_iface_from.id, kpm_iface_to.id)


def kpm_connections_from_design_descr(
        design_descr: DesignDescription,
        nodes: List[KPMDataflowNode]) -> List[KPMDataflowConnection]:

    """ Generate KPM connections based on the data from DesignDescription.
    We also need a list of previously generated KPM dataflow nodes, because the
    connections in KPM are specified using id's of their interfaces
    """
    connections = []
    for conn in design_descr.ports_conn:
        if conn.port_from is None:
            node = _get_dataflow_node_by_name(conn.port_to.ip_name, nodes)
            if node is None:
                continue
            iface = _get_dataflow_interface_by_name(conn.port_to.name, node)
            iface.value = conn.default
        else:
            connection = _create_kpm_dataflow_connection(
                conn.port_from.name,
                conn.port_from.ip_name,
                conn.port_to.name,
                conn.port_to.ip_name,
                nodes)
            if connection is not None:
                connections.append(connection)

    for conn in design_descr.interfaces_conn:
        connection = _create_kpm_dataflow_connection(
            conn.interface_from.name,
            conn.interface_from.ip_name,
            conn.interface_to.name,
            conn.interface_to.ip_name,
            nodes)
        if connection is not None:
            connections.append(connection)

    return connections


def kpm_dataflow_from_design_descr(
        design_descr: DesignDescription,
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
