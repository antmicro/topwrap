# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import logging
import os
from typing import List
from time import time
from .kpm_common import (
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    EXT_INOUT_NAME,
    get_metanode_property_value
)


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
    KPM_DIR_INPUT = 'input'
    KPM_DIR_OUTPUT = 'output'
    KPM_DIR_INOUT = 'inout'
    __EXT_IFACE_NAME = 'external'

    def __init__(self, name: str, direction: str):
        if direction not in [
                KPMDataflowNodeInterface.KPM_DIR_INPUT,
                KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
                KPMDataflowNodeInterface.KPM_DIR_INOUT]:
            raise ValueError(f"Invalid interface direction: {direction}")

        generator = IDGenerator()
        self.id = "ni_" + generator.generate_id()
        self.name = name
        self.direction = direction

    @staticmethod
    def new_external_interface(direction: str) -> KPMDataflowNodeInterface:
        return KPMDataflowNodeInterface(
            KPMDataflowNodeInterface.__EXT_IFACE_NAME, direction)


class KPMDataflowNodeProperty:
    KPM_EXT_PROP_NAME = 'External Name'

    def __init__(self, name: str, value: str):
        generator = IDGenerator()
        self.id = generator.generate_id()
        self.name = name
        self.value = value

    @staticmethod
    def new_external_property(value: str) -> KPMDataflowNodeProperty:
        return KPMDataflowNodeProperty(
            KPMDataflowNodeProperty.KPM_EXT_PROP_NAME,
            value
        )


class KPMDataflowNode:
    __default_width = 200

    def __init__(self,
                 name: str,
                 type: str,
                 properties: List[KPMDataflowNodeProperty],
                 interfaces: List[KPMDataflowNodeInterface]) -> None:

        generator = IDGenerator()
        self.id = "node_" + generator.generate_id()
        self.name = name
        self.type = type
        self.properties = properties
        self.interfaces = interfaces

    @staticmethod
    def new_external_node(
            node_name: str,
            property_name: str) -> KPMDataflowNode:

        if node_name not in [EXT_OUTPUT_NAME, EXT_INPUT_NAME, EXT_INOUT_NAME]:
            raise ValueError(f"Invalid external node name: {node_name}")

        interface_dir_by_node_name = {
            EXT_OUTPUT_NAME: KPMDataflowNodeInterface.KPM_DIR_INPUT,
            EXT_INPUT_NAME: KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
            EXT_INOUT_NAME: KPMDataflowNodeInterface.KPM_DIR_INOUT
        }
        return KPMDataflowNode(
            node_name,
            node_name,
            [KPMDataflowNodeProperty.new_external_property(property_name)],
            [KPMDataflowNodeInterface.new_external_interface(
                interface_dir_by_node_name[node_name]
            )]
        )

    def to_json_format(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "interfaces": [
                {
                    "name": interface.name,
                    "id": interface.id,
                    "direction": interface.direction,
                    "connectionSide": "left"
                    if (interface.direction
                        == KPMDataflowNodeInterface.KPM_DIR_INPUT)
                    else "right"
                } for interface in self.interfaces
            ],
            "position": {
                "x": 0,
                "y": 0
            },
            "width": KPMDataflowNode.__default_width,
            "twoColumn": False,
            "properties": [
                {
                    "name": property.name,
                    "id": property.id,
                    "value": property.value
                }
                for property in self.properties
            ]
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
    """ Return a node of type `type` from specification
    """
    for node in specification['nodes']:
        if type == node['type']:
            return node
    logging.warning(f'Node type "{type}" not found in specification')


def _ipcore_param_to_kpm_value(param) -> str:
    """ Return a string representing an IP core parameter,
    that will be placed in dataflow node property textbox
    """
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
            prop['name']: KPMDataflowNodeProperty(
                prop['name'], prop['default']
            )
            for prop in spec_node['properties']
        }
        if 'parameters' in ip.keys():
            for (param_name, param_val) in ip['parameters'].items():
                if param_name in properties.keys():
                    properties[param_name].value = _ipcore_param_to_kpm_value(
                        param_val
                    )
                else:
                    logging.warning(
                        f"Parameter '{param_name}'"
                        f"not found in node {ip_name}"
                    )

        interfaces = [
            KPMDataflowNodeInterface(interface['name'], interface['direction'])
            for interface in spec_node['interfaces']
        ]

        nodes.append(KPMDataflowNode(ip_name, ip_type,
                     list(properties.values()), interfaces))
    return nodes


def _get_dataflow_interface_by_name(
        name: str,
        node_name: str,
        nodes: List[KPMDataflowNode]) -> KPMDataflowNodeInterface:
    """ Find `name` interface of a node
    (representing an IP core) named `node_name`.
    """
    for node in nodes:
        if node.name == node_name:
            for iface in node.interfaces:
                if iface.name == name:
                    return iface
            logging.warning(
                f"Interface '{name}' not found in node {node_name}")
            return
    logging.warning(f"Node '{node_name}' not found")


def _parse_design_descr_connections(
        conns_dict: dict,
        nodes: List[KPMDataflowNode]) -> List[KPMDataflowConnection]:
    """ Helper function for parsing "ports" or "interfaces" section of
    a design description yaml into a list of KPMDataflowConnection
    """
    connections = []
    for ip_conns in conns_dict.items():
        for conn in ip_conns[1].items():
            if isinstance(conn[1], list):
                kpm_iface_from = _get_dataflow_interface_by_name(
                    conn[1][1], conn[1][0], nodes)
                kpm_iface_to = _get_dataflow_interface_by_name(
                    conn[0], ip_conns[0], nodes)
                if kpm_iface_from is not None and kpm_iface_to is not None:
                    connections.append(KPMDataflowConnection(
                        kpm_iface_from.id, kpm_iface_to.id))
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

    return (_parse_design_descr_connections(port_conns, nodes) +
            _parse_design_descr_connections(interface_conns, nodes))


def kpm_metanodes_from_design_descr(
        design_descr: dict) -> List[KPMDataflowNode]:
    """ Generate a list of external metanodes based on the contents of
    "externals" section of Topwrap's design description
    """
    if 'external' not in design_descr.keys():
        return []

    metanodes = []
    dir_to_metanode_type = {
        'in': EXT_INPUT_NAME,
        'out': EXT_OUTPUT_NAME,
        'inout': EXT_INOUT_NAME
    }

    for conn_type in design_descr['external'].keys():
        for dir in design_descr['external'][conn_type].keys():
            for external_name in design_descr['external'][conn_type][dir]:
                metanodes.append(KPMDataflowNode.new_external_node(
                    dir_to_metanode_type[dir], external_name))

    return metanodes


def _find_dataflow_metanode_by_external_name(
        metanodes: List[KPMDataflowNode],
        external_name: str) -> KPMDataflowNode:

    for metanode in metanodes:
        prop_val = get_metanode_property_value(metanode.to_json_format())
        if prop_val == external_name:
            return metanode
    logging.warning(f"External port/interface '{external_name}'"
                    "not found in design description")


def _create_external_connection(
        kpm_interface: KPMDataflowNodeInterface,
        kpm_metanode: KPMDataflowNode) -> KPMDataflowConnection:

    kpm_meta_interface = kpm_metanode.interfaces[0]

    iface_dir = kpm_interface.direction
    ext_dir = kpm_meta_interface.direction

    if (iface_dir == KPMDataflowNodeInterface.KPM_DIR_OUTPUT and
        ext_dir != KPMDataflowNodeInterface.KPM_DIR_INPUT) or \
        (iface_dir == KPMDataflowNodeInterface.KPM_DIR_INPUT and
         ext_dir != KPMDataflowNodeInterface.KPM_DIR_OUTPUT) or \
        (iface_dir == KPMDataflowNodeInterface.KPM_DIR_INOUT and
         ext_dir != KPMDataflowNodeInterface.KPM_DIR_INOUT):
        logging.warning("Incorrect external direction for"
                        f"'{kpm_metanode.properties[0].value}'")
    else:
        id_from = kpm_interface.id
        id_to = kpm_meta_interface.id
        if iface_dir == KPMDataflowNodeInterface.KPM_DIR_INPUT:
            id_from, id_to = id_to, id_from

        return KPMDataflowConnection(id_from, id_to)


def kpm_metanodes_connections_from_design_descr(
        design_descr: dict,
        nodes: List[KPMDataflowNode],
        metanodes: List[KPMDataflowNode]) -> List[KPMDataflowConnection]:
    """ Create a list of connections between external metanodes and
    appropriate  nodes' interfaces, based on the contents of "externals"
    section of Topwrap's design description
    """
    connections = []

    for conn_section in ['ports', 'interfaces']:
        if conn_section not in design_descr.keys():
            continue
        for ip_name in design_descr[conn_section].keys():
            for iface_name in design_descr[conn_section][ip_name].keys():
                ext_name = design_descr[conn_section][ip_name][iface_name]
                if isinstance(ext_name, str):
                    kpm_interface = _get_dataflow_interface_by_name(
                        iface_name, ip_name, nodes)
                    kpm_metanode = _find_dataflow_metanode_by_external_name(
                        metanodes, ext_name)
                    if kpm_interface is not None and kpm_metanode is not None:
                        connections.append(_create_external_connection(
                            kpm_interface, kpm_metanode))

    return [conn for conn in connections if conn is not None]


def kpm_dataflow_from_design_descr(
        design_descr: dict,
        specification: dict) -> dict:
    """ Generate Pipeline Manager dataflow from a design description
    in Topwrap's yaml format
    """
    nodes = kpm_nodes_from_design_descr(design_descr, specification)
    metanodes = kpm_metanodes_from_design_descr(design_descr)
    connections = kpm_connections_from_design_descr(design_descr, nodes)
    ext_connections = kpm_metanodes_connections_from_design_descr(
        design_descr, nodes, metanodes)
    generator = IDGenerator()
    return {
        "graph": {
            "id": generator.generate_id(),
            "nodes": [
                node.to_json_format() for node in nodes
            ] + [
                metanode.to_json_format() for metanode in metanodes
            ],
            "connections": [
                connection.to_json_format() for connection in connections
            ] + [
                ext_connection.to_json_format()
                for ext_connection in ext_connections
            ],
            "inputs": [],
            "outputs": []
        },
        "graphTemplates": []
    }
