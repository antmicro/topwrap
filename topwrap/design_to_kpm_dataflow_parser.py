# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os
from time import time
from typing import List

from .design import get_hierarchies_names, get_interconnects_names, get_ipcores_names
from .kpm_common import (
    CONST_NAME,
    EXT_INOUT_NAME,
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    get_metanode_property_value,
)


class IDGenerator(object):
    """ID generator implementation just as in BaklavaJS"""

    __counter = 0

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(IDGenerator, cls).__new__(cls)
        return cls.instance

    def generate_id(self) -> str:
        result = str(int(time() * 1000)) + str(IDGenerator.__counter)
        IDGenerator.__counter += 1
        return result


class KPMDataflowNodeInterface:
    KPM_DIR_INPUT = "input"
    KPM_DIR_OUTPUT = "output"
    KPM_DIR_INOUT = "inout"

    def __init__(self, name: str, direction: str, value: str = None):
        if direction not in [
            KPMDataflowNodeInterface.KPM_DIR_INPUT,
            KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
            KPMDataflowNodeInterface.KPM_DIR_INOUT,
        ]:
            raise ValueError(f"Invalid interface direction: {direction}")

        generator = IDGenerator()
        self.id = "ni_" + generator.generate_id()
        self.name = name
        self.direction = direction
        self.value = value


class KPMDataflowMetanodeInterface(KPMDataflowNodeInterface):
    EXT_IFACE_NAME = "external"
    CONST_IFACE_NAME = "constant"

    def __init__(self, name, direction, **kwargs):
        if name not in [self.EXT_IFACE_NAME, self.CONST_IFACE_NAME]:
            raise ValueError(f"Invalid metanode interface name: {name}")

        super().__init__(name, direction, **kwargs)


class KPMDataflowNodeProperty:
    def __init__(self, name: str, value: str):
        generator = IDGenerator()
        self.id = generator.generate_id()
        self.name = name
        self.value = value


class KPMDataflowMetanodeProperty(KPMDataflowNodeProperty):
    KPM_EXT_PROP_NAME = "External Name"
    KPM_CONST_VALUE_PROP_NAME = "Constant Value"

    def __init__(self, name, value):
        if name not in [self.KPM_EXT_PROP_NAME, self.KPM_CONST_VALUE_PROP_NAME]:
            raise ValueError(f"Invalid metanode property name: {name}")

        super().__init__(name, value)


class KPMDataflowNode:
    __default_width = 200

    def __init__(
        self,
        name: str,
        type: str,
        properties: List[KPMDataflowNodeProperty],
        interfaces: List[KPMDataflowNodeInterface],
    ) -> None:
        generator = IDGenerator()
        self.id = "node_" + generator.generate_id()
        self.name = name
        self.type = type
        self.properties = properties
        self.interfaces = interfaces

    def to_json_format(self) -> dict:
        return {
            "name": self.type,
            "id": self.id,
            "instanceName": self.name,
            "interfaces": [
                {
                    "name": interface.name,
                    "id": interface.id,
                    "direction": interface.direction,
                    "connectionSide": (
                        "left"
                        if (interface.direction == KPMDataflowNodeInterface.KPM_DIR_INPUT)
                        else "right"
                    ),
                }
                for interface in self.interfaces
            ],
            "position": {"x": 0, "y": 0},
            "width": KPMDataflowNode.__default_width,
            "properties": [
                {"name": property.name, "id": property.id, "value": property.value}
                for property in self.properties
            ],
        }


class KPMDataflowMetanode(KPMDataflowNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class KPMDataflowExternalMetanode(KPMDataflowMetanode):
    def __init__(self, node_name: str, property_name: str):
        if node_name not in [EXT_OUTPUT_NAME, EXT_INPUT_NAME, EXT_INOUT_NAME]:
            raise ValueError(f"Invalid external node name: {node_name}")

        interface_dir_by_node_name = {
            EXT_OUTPUT_NAME: KPMDataflowNodeInterface.KPM_DIR_INPUT,
            EXT_INPUT_NAME: KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
            EXT_INOUT_NAME: KPMDataflowNodeInterface.KPM_DIR_INOUT,
        }

        super().__init__(
            name=node_name,
            type=node_name,
            properties=[
                KPMDataflowMetanodeProperty(
                    KPMDataflowMetanodeProperty.KPM_EXT_PROP_NAME, property_name
                )
            ],
            interfaces=[
                KPMDataflowMetanodeInterface(
                    KPMDataflowMetanodeInterface.EXT_IFACE_NAME,
                    interface_dir_by_node_name[node_name],
                )
            ],
        )


class KPMDataflowConstantMetanode(KPMDataflowMetanode):
    def __init__(self, value: int):
        super().__init__(
            name=CONST_NAME,
            type=CONST_NAME,
            properties=[
                KPMDataflowMetanodeProperty(
                    KPMDataflowMetanodeProperty.KPM_CONST_VALUE_PROP_NAME, value
                )
            ],
            interfaces=[
                KPMDataflowMetanodeInterface(
                    KPMDataflowMetanodeInterface.CONST_IFACE_NAME,
                    KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
                    value=value,
                )
            ],
        )


class KPMDataflowConnection:
    def __init__(self, id_from: str, id_to: str) -> None:
        generator = IDGenerator()
        self.id = generator.generate_id()
        self.id_from = id_from
        self.id_to = id_to

    def to_json_format(self) -> dict:
        return {"id": self.id, "from": self.id_from, "to": self.id_to}


def _get_specification_node_by_type(type: str, specification: dict) -> dict:
    """Return a node of type `type` from specification"""
    for node in specification["nodes"]:
        if type == node["layer"]:
            return node
    logging.warning(f'Node type "{type}" not found in specification')


def _ipcore_param_to_kpm_value(param) -> str:
    """Return a string representing an IP core parameter,
    that will be placed in dataflow node property textbox
    """
    if isinstance(param, str):
        return param
    elif isinstance(param, int):
        return str(param)
    elif isinstance(param, dict) and param.keys() == {"value", "width"}:
        width = str(param["width"])
        value = hex(param["value"])[2:]
        return width + "'h" + value


def kpm_nodes_from_design_descr(design_descr: dict, specification: dict) -> List[KPMDataflowNode]:
    """Generate KPM dataflow nodes based on Topwrap's design
    description yaml (e.g. generated from YAML design description)
    and already loaded KPM specification.
    """
    nodes = []
    ips = design_descr["ips"]
    design = design_descr["design"]
    parameters = design["parameters"] if "parameters" in design.keys() else dict()

    hier_names = get_hierarchies_names(design)
    if hier_names:
        logging.warning(
            f"Imported design contains hierarchies ({hier_names}) which are not "
            "supported yet. The imported design will be incomplete"
        )
    interconnect_names = get_interconnects_names(design)
    if interconnect_names:
        logging.warning(
            f"Imported design contains interconnects ({interconnect_names}) which are not "
            "supported yet. The imported design will be incomplete"
        )

    for ip_name in get_ipcores_names(design):
        ports = design["ports"][ip_name]
        ip_type = os.path.splitext(os.path.basename(ips[ip_name]["file"]))[0]
        spec_node = _get_specification_node_by_type(ip_type, specification)
        if spec_node is None:
            continue

        kpm_properties = {
            prop["name"]: KPMDataflowNodeProperty(prop["name"], prop["default"])
            for prop in spec_node["properties"]
        }
        if ip_name in parameters.keys():
            for param_name, param_val in parameters[ip_name].items():
                if param_name in kpm_properties.keys():
                    kpm_properties[param_name].value = _ipcore_param_to_kpm_value(param_val)
                else:
                    logging.warning(f"Parameter '{param_name}'" f"not found in node {ip_name}")

        interfaces = []
        for interface in spec_node["interfaces"]:
            dir = interface["direction"]
            value = (
                None
                if ((dir != "input") or ("iface" in interface["type"][0]))
                else ports[interface["name"]]
            )
            interfaces.append(KPMDataflowNodeInterface(interface["name"], dir, value))

        nodes.append(KPMDataflowNode(ip_name, ip_type, list(kpm_properties.values()), interfaces))
    return nodes


def _get_dataflow_interface_by_name(
    name: str, node_name: str, nodes: List[KPMDataflowNode]
) -> KPMDataflowNodeInterface:
    """Find `name` interface of a node
    (representing an IP core) named `node_name`.
    """
    for node in nodes:
        if node.name == node_name:
            for iface in node.interfaces:
                if iface.name == name:
                    return iface
            logging.warning(f"Interface '{name}' not found in node {node_name}")
            return
    logging.warning(f"Node '{node_name}' not found")


def _get_flattened_connections(design_descr: dict) -> list:
    """Helper function to get a list of flattened connections
    from a design description yaml.
    """
    conn_descrs = []
    design = design_descr["design"]

    for sec in ["ports", "interfaces"]:
        if sec not in design.keys():
            continue
        for ip_name in design[sec].keys():
            for port_iface_name, value in design[sec][ip_name].items():
                if isinstance(value, int):
                    connection = "Constant"
                else:
                    connection = design[sec][ip_name][port_iface_name]

                conn_descrs.append(
                    {
                        "ip_name": ip_name,
                        "port_iface_name": port_iface_name,
                        "connection": connection,
                    }
                )
    return conn_descrs


def _get_inout_connections(ports: dict) -> list:
    conn_descrs = []
    inouts = ports["inout"] if "inout" in ports else {}

    for [ip_name, port_name] in inouts:
        conn_descrs.append(
            {"ip_name": ip_name, "port_iface_name": port_name, "connection": port_name}
        )
    return conn_descrs


def _get_external_connections(design_descr: dict) -> list:
    """Get connections to externals from 'ports' and 'interfaces'
    sections of design description.
    """
    ext_connections = list(
        filter(
            lambda conn_descr: isinstance(conn_descr["connection"], str),
            _get_flattened_connections(design_descr),
        )
    ) + _get_inout_connections(design_descr["external"]["ports"])

    # `ext_connections` is now a list of all the external connections gathered
    # from a design yaml. Each such connection is in format:
    # `{'ip_name': str, 'port_iface_name': str, 'connection': str}`
    # where 'connection' represents a name of the external port/interface

    return [
        {
            "ip_name": conn["ip_name"],
            "port_iface_name": conn["port_iface_name"],
            "external_name": conn["connection"],
        }
        for conn in ext_connections
        if conn["ip_name"] not in get_hierarchies_names(design_descr["design"])
        # skip external connections from/to hierarchies
    ]


def _get_ipcores_connections(design_descr: dict) -> list:
    """Get connections between IP cores from 'ports' and 'interfaces'
    sections of design description.
    """

    def _is_ipcore_connection(conn_descr: dict) -> bool:
        """Check if a connection is between two IP cores. `conn_descr` is here a dict in format:
        `{"ip_name": str, "port_iface_name": str, "connection": list|int|str }`
        """
        if not isinstance(conn_descr["connection"], list):
            return False
        if conn_descr["ip_name"] in get_hierarchies_names(design_descr["design"]):
            return False
        if conn_descr["connection"][0] in get_hierarchies_names(design_descr["design"]):
            return False
        return True

    ipcores_connections = list(
        filter(_is_ipcore_connection, _get_flattened_connections(design_descr))
    )

    # `ipcores_connections` is now a list of all the connections between
    # IP cores gathered from a design yaml. Each such connection is in format:
    # `{'ip_name': str, 'port_iface_name': str, 'connection': [str, str]}`
    # where conn['connection'][0] is an IP name and conn['connection'][1] is
    # a port/interface name from which the connection originates

    return [
        {
            "ip_to_name": conn["ip_name"],
            "port_iface_to_name": conn["port_iface_name"],
            "ip_from_name": conn["connection"][0],
            "port_iface_from_name": conn["connection"][1],
        }
        for conn in ipcores_connections
    ]


def _create_connection(
    kpm_iface_from: KPMDataflowNodeInterface, kpm_iface_to: KPMDataflowNodeInterface
) -> KPMDataflowConnection:
    dir_from = kpm_iface_from.direction
    dir_to = kpm_iface_to.direction

    if (
        (
            dir_from == KPMDataflowNodeInterface.KPM_DIR_OUTPUT
            and dir_to != KPMDataflowNodeInterface.KPM_DIR_INPUT
        )
        or (
            dir_from == KPMDataflowNodeInterface.KPM_DIR_INPUT
            and dir_to != KPMDataflowNodeInterface.KPM_DIR_OUTPUT
        )
        or (
            dir_from == KPMDataflowNodeInterface.KPM_DIR_INOUT
            and dir_to != KPMDataflowNodeInterface.KPM_DIR_INOUT
        )
    ):
        logging.warning(
            "Port/interface direction mismatch for connection: "
            f"'{kpm_iface_from.name}<->{kpm_iface_to.name}'"
        )
    else:
        return KPMDataflowConnection(kpm_iface_from.id, kpm_iface_to.id)


def kpm_connections_from_design_descr(
    design_descr: dict, nodes: List[KPMDataflowNode]
) -> List[KPMDataflowConnection]:
    """Generate KPM connections based on the data from `design_descr`.
    We also need a list of previously generated KPM dataflow nodes, because the
    connections in KPM are specified using id's of their interfaces
    """
    result = []
    _conns = _get_ipcores_connections(design_descr)

    for conn in _conns:
        kpm_iface_from = _get_dataflow_interface_by_name(
            conn["port_iface_from_name"], conn["ip_from_name"], nodes
        )
        kpm_iface_to = _get_dataflow_interface_by_name(
            conn["port_iface_to_name"], conn["ip_to_name"], nodes
        )
        if kpm_iface_from is not None and kpm_iface_to is not None:
            result.append(_create_connection(kpm_iface_from, kpm_iface_to))
    return [conn for conn in result if conn is not None]


def kpm_external_metanodes_from_design_descr(design_descr: dict) -> List[KPMDataflowNode]:
    """Generate a list of external metanodes based on the contents of
    'external' section of Topwrap's design description
    """
    if "external" not in design_descr.keys():
        return []

    metanodes = []
    dir_to_metanode_type = {"in": EXT_INPUT_NAME, "out": EXT_OUTPUT_NAME, "inout": EXT_INOUT_NAME}

    for conn_type in design_descr["external"].keys():
        for dir in design_descr["external"][conn_type].keys():
            for external_name in design_descr["external"][conn_type][dir]:
                if dir == "inout":
                    _, ext_name = external_name
                else:
                    ext_name = external_name
                metanodes.append(KPMDataflowExternalMetanode(dir_to_metanode_type[dir], ext_name))

    return metanodes


def kpm_constant_metanodes_from_nodes(nodes: list) -> List[KPMDataflowNode]:
    """Generate a list of constant metanodes based on values assigned to ip core
    ports of Topwrap's design description
    """
    metanodes = []
    created = []

    for node in nodes:
        for port in node.interfaces:
            value = port.value

            if not isinstance(value, int):
                continue

            if value in created:
                continue

            metanodes.append(KPMDataflowConstantMetanode(value))
            created.append(value)

    return metanodes


def kpm_constant_metanodes_from_design_descr(
    design_descr: dict, specification: dict
) -> List[KPMDataflowNode]:
    """Generate a list of constant metanodes based on values assigned to ip core
    ports of Topwrap's design description
    """
    nodes = kpm_nodes_from_design_descr(design_descr, specification)
    return kpm_constant_metanodes_from_nodes(nodes)


def kpm_metanodes_from_design_descr(
    design_descr: dict, specification: dict
) -> List[KPMDataflowNode]:
    """Generate a list of all metanodes based on values assigned to ip core
    ports and an 'external' section of Topwrap's design description
    """
    externals = kpm_external_metanodes_from_design_descr(design_descr)
    constants = kpm_constant_metanodes_from_design_descr(design_descr, specification)

    return externals + constants


def _find_dataflow_metanode_by_external_name(
    metanodes: List[KPMDataflowNode], external_name: str
) -> KPMDataflowNode:
    for metanode in metanodes:
        prop_val = get_metanode_property_value(metanode.to_json_format())
        if prop_val == external_name:
            return metanode
    logging.warning(f"External port/interface '{external_name}' not found in design description")


def _find_dataflow_metanode_by_constant_value(
    metanodes: List[KPMDataflowNode], value: int
) -> KPMDataflowNode:
    for metanode in metanodes:
        prop_val = get_metanode_property_value(metanode.to_json_format())
        if prop_val == value:
            return metanode
    logging.warning(f"Constant value '{value}' not found in design description")


def kpm_metanodes_connections_from_design_descr(
    design_descr: dict, nodes: List[KPMDataflowNode], metanodes: List[KPMDataflowNode]
) -> List[KPMDataflowConnection]:
    """Create a list of connections between external metanodes and
    appropriate  nodes' interfaces, based on the contents of 'external'
    section of Topwrap's design description
    """
    result = []
    _external_conns = _get_external_connections(design_descr)

    for ext_conn in _external_conns:
        kpm_interface = _get_dataflow_interface_by_name(
            ext_conn["port_iface_name"], ext_conn["ip_name"], nodes
        )

        if isinstance(kpm_interface.value, int):
            if kpm_interface.direction != KPMDataflowNodeInterface.KPM_DIR_INPUT:
                logging.warning("Cannot assign output port to constant value")
                continue

            kpm_metanode = _find_dataflow_metanode_by_constant_value(metanodes, kpm_interface.value)
        else:
            kpm_metanode = _find_dataflow_metanode_by_external_name(
                metanodes, ext_conn["external_name"]
            )

        if kpm_interface is not None and kpm_metanode is not None:
            # Metanodes have exactly 1 interface; hence we can take 0th index
            # of the `interfaces` array of a metanode to access the interface.
            result.append(_create_connection(kpm_interface, kpm_metanode.interfaces[0]))
    return [conn for conn in result if conn is not None]


def kpm_dataflow_from_design_descr(design_descr: dict, specification: dict) -> dict:
    """Generate Pipeline Manager dataflow from a design description
    in Topwrap's yaml format
    """
    nodes = kpm_nodes_from_design_descr(design_descr, specification)
    metanodes = kpm_metanodes_from_design_descr(design_descr, specification)
    connections = kpm_connections_from_design_descr(design_descr, nodes)
    metanodes_connections = kpm_metanodes_connections_from_design_descr(
        design_descr, nodes, metanodes
    )
    generator = IDGenerator()
    return {
        "graph": {
            "id": generator.generate_id(),
            "nodes": [node.to_json_format() for node in nodes]
            + [metanode.to_json_format() for metanode in metanodes],
            "connections": [connection.to_json_format() for connection in connections]
            + [ext_connection.to_json_format() for ext_connection in metanodes_connections],
            "inputs": [],
            "outputs": [],
        },
        "subgraphs": [],
        "version": "20230830.11",
    }
