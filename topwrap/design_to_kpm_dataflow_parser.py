# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import PurePath
from time import time
from typing import Dict, List, Optional, Tuple

from typing_extensions import override

from .design import get_interconnects_names, get_ipcores_names
from .kpm_common import (
    CONST_NAME,
    EXT_INOUT_NAME,
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    get_metanode_property_value,
)


@dataclass
class SubgraphMaps:
    """Helper class for dicts that are used during subgraph creation"""

    interface_name_id_map: Dict[str, str] = field(default_factory=dict)
    subgraph_name_id_map: Dict[str, str] = field(default_factory=dict)

    def update_maps(self, submaps_update: SubgraphMaps) -> None:
        self.interface_name_id_map.update(submaps_update.interface_name_id_map)
        self.subgraph_name_id_map.update(submaps_update.subgraph_name_id_map)


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

    kpm_direction_extensions_dict = {
        "in": KPM_DIR_INPUT,
        "out": KPM_DIR_OUTPUT,
        "inout": KPM_DIR_INOUT,
    }

    def __init__(self, name: str, direction: str, value: Optional[str] = None):
        if direction not in self.kpm_direction_extensions_dict.values():
            raise ValueError(f"Invalid interface direction: {direction}")

        self.id = "ni_" + IDGenerator().generate_id()
        self.name = name
        self.direction = direction
        self.value = value
        self.external_name = None

    def to_json_format(self, index: int):
        json_format = {
            "name": self.name,
            "id": self.id,
            "direction": self.direction,
            "side": ("left" if (self.direction == self.KPM_DIR_INPUT) else "right"),
            "sidePosition": index,
        }
        if self.external_name is not None:
            json_format["externalName"] = self.external_name
        return json_format


class KPMDataflowSubgraphnodeInterface(KPMDataflowNodeInterface):
    def __init__(self, name, direction):
        if direction not in KPMDataflowNodeInterface.kpm_direction_extensions_dict.keys():
            raise ValueError(f"Invalid subgraph direction: {direction}")
        super().__init__(name, KPMDataflowNodeInterface.kpm_direction_extensions_dict[direction])


class KPMDataflowMetanodeInterface(KPMDataflowNodeInterface):
    EXT_IFACE_NAME = "external"
    CONST_IFACE_NAME = "constant"

    def __init__(self, name, direction, **kwargs):
        if name not in [self.EXT_IFACE_NAME, self.CONST_IFACE_NAME]:
            raise ValueError(f"Invalid metanode interface name: {name}")

        super().__init__(name, direction, **kwargs)


class KPMDataflowNodeProperty:
    def __init__(self, name: str, value: str):
        self.id = IDGenerator().generate_id()
        self.name = name
        self.value = value

    def to_json_format(self):
        return {"name": self.name, "id": self.id, "value": self.value}


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
        self.id = "node_" + IDGenerator().generate_id()
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
                interface.to_json_format(index) for index, interface in enumerate(self.interfaces)
            ],
            "position": {"x": 0, "y": 0},
            "width": KPMDataflowNode.__default_width,
            "properties": [property.to_json_format() for property in self.properties],
        }


class KPMDataflowSubgraphnode(KPMDataflowNode):
    DUMMY_NAME_BASE = "New Graph Node"

    def __init__(
        self,
        name: str,
        properties: List[KPMDataflowNodeProperty],
        interfaces: List[KPMDataflowNodeInterface],
        subgraph: str,
    ) -> None:
        super().__init__(name, self.DUMMY_NAME_BASE, properties, interfaces)
        self.subgraph = subgraph

    @override
    def to_json_format(self) -> dict:
        node_json = super().to_json_format()
        node_json["subgraph"] = self.subgraph

        return node_json


class KPMDataflowMetanode(KPMDataflowNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class KPMDataflowExternalMetanode(KPMDataflowMetanode):
    @staticmethod
    def valid_node_name(node_name: str) -> bool:
        return node_name in [EXT_OUTPUT_NAME, EXT_INPUT_NAME, EXT_INOUT_NAME]

    interface_dir_by_node_name = {
        EXT_OUTPUT_NAME: KPMDataflowNodeInterface.KPM_DIR_INPUT,
        EXT_INPUT_NAME: KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
        EXT_INOUT_NAME: KPMDataflowNodeInterface.KPM_DIR_INOUT,
    }

    def __init__(self, node_name: str, property_name: str):
        if not self.valid_node_name(node_name):
            raise ValueError(f"Invalid external node name: {node_name}")

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
                    self.interface_dir_by_node_name[node_name],
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
                    KPMDataflowMetanodeProperty.KPM_CONST_VALUE_PROP_NAME, str(value)
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


class KPMDataflowGraph:
    def __init__(
        self, connections: List[KPMDataflowConnection], nodes: List[KPMDataflowNode], id=None
    ):
        self.connections = connections
        self.nodes = nodes
        self.id = id if id else IDGenerator().generate_id()

    def to_json_format(self) -> dict:
        return {
            "id": self.id,
            "scaling": 1,
            "nodes": [node.to_json_format() for node in self.nodes],
            "connections": [connection.to_json_format() for connection in self.connections],
        }


def _get_specification_node_by_type(type: str, specification: dict) -> Optional[dict]:
    """Return a node of type `type` from specification"""
    for node in specification["nodes"]:
        if type == node["layer"]:
            return node
    logging.warning(f'Node type "{type}" not found in specification')


def _ipcore_param_to_kpm_value(param) -> str:
    """Return a string representing an IP core parameter,
    that will be placed in dataflow node property textbox
    """
    if isinstance(param, int):
        return str(param)
    if isinstance(param, str):
        return param
    elif isinstance(param, dict) and param.keys() == {"value", "width"}:
        width = str(param["width"])
        value = hex(param["value"])[2:]
        return width + "'h" + value
    else:
        logging.warning(f"Param type: {type(param)} was not recognized")
        return str(param)


def get_kpm_nodes_from_core_names(
    design_descr: dict, specification: dict, names: set, ips: dict
) -> List[KPMDataflowNode]:
    """Return list of nodes that will be created based on design and specification from names list"""
    nodes = []
    design = design_descr["design"]
    parameters = design["parameters"] if "parameters" in design.keys() else dict()
    for ip_name in names:
        ports = design["ports"][ip_name]
        ip_type = PurePath(ips[ip_name]["file"]).stem
        spec_node = _get_specification_node_by_type(ip_type, specification)
        if spec_node is None:
            continue

        kpm_properties = {
            prop["name"]: KPMDataflowNodeProperty(prop["name"], prop["default"])
            for prop in spec_node.get("properties", [])
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


def kpm_nodes_from_design_descr(
    design_descr: dict, specification: dict, ips: dict
) -> List[KPMDataflowNode]:
    """Generate KPM dataflow nodes based on Topwrap's design
    description yaml (e.g. generated from YAML design description)
    and already loaded KPM specification.
    """

    design = design_descr["design"]
    interconnect_names = get_interconnects_names(design)
    if interconnect_names:
        logging.warning(
            f"Imported design contains interconnects ({interconnect_names}) which are not "
            "supported yet. The imported design will be incomplete"
        )

    return get_kpm_nodes_from_core_names(
        design_descr, specification, get_ipcores_names(design), ips
    )


def _get_dataflow_interface_by_name(
    name: str, node_name: str, nodes: List[KPMDataflowNode]
) -> Optional[KPMDataflowNodeInterface]:
    """Find `name` interface of a node
    (representing an IP core) named `node_name`.
    """
    for node in nodes:
        if node.name == node_name:
            for iface in node.interfaces:
                if iface.name == name:
                    return iface
            logging.warning(f"Interface '{name}' not found in node {node_name}")
    logging.warning(f"Node '{node_name}' not found")


def _get_flattened_connections(design_descr: dict) -> List[dict]:
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
                    connection = CONST_NAME
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


def _get_inout_connections(ports: dict) -> List[dict]:
    """Return all inout connections from ports"""
    conn_descrs = []
    inouts = ports["inout"] if "inout" in ports else {}

    for [ip_name, port_name] in inouts:
        conn_descrs.append(
            {"ip_name": ip_name, "port_iface_name": port_name, "connection": port_name}
        )
    return conn_descrs


def _get_external_connections(design_descr: dict) -> List[dict]:
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
    ]


def _get_ipcores_connections(design_descr: dict) -> List[dict]:
    """Get connections between IP cores from 'ports' and 'interfaces'
    sections of design description.
    """

    def _is_ipcore_connection(conn_descr: dict) -> bool:
        """Check if a connection is between two IP cores.
        If it's not a list then it is some external connection"""
        return isinstance(conn_descr["connection"], list)

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
) -> Optional[KPMDataflowConnection]:
    """Create a connection between two interfaces"""

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
    design_descr: dict,
    all_nodes: List[KPMDataflowNode],
) -> List[KPMDataflowConnection]:
    """Generate KPM connections based on the data from `design_descr`.
    We also need a list of previously generated KPM dataflow nodes, because the
    connections in KPM are specified using id's of their interfaces
    """
    result = []

    _conns = _get_ipcores_connections(design_descr)

    for conn in _conns:
        kpm_iface_from = _get_dataflow_interface_by_name(
            conn["port_iface_from_name"], conn["ip_from_name"], all_nodes
        )
        kpm_iface_to = _get_dataflow_interface_by_name(
            conn["port_iface_to_name"], conn["ip_to_name"], all_nodes
        )
        if kpm_iface_from is not None and kpm_iface_to is not None:
            result.append(_create_connection(kpm_iface_from, kpm_iface_to))
    return [conn for conn in result if conn is not None]


def kpm_external_metanodes_from_design_descr(
    design_descr: dict,
) -> List[KPMDataflowExternalMetanode]:
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


def kpm_constant_metanodes_from_nodes(
    nodes: List[KPMDataflowNode],
) -> List[KPMDataflowConstantMetanode]:
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
) -> List[KPMDataflowConstantMetanode]:
    """Generate a list of constant metanodes based on values assigned to ip core
    ports of Topwrap's design description
    """
    nodes = kpm_nodes_from_design_descr(design_descr, specification, design_descr["ips"])
    return kpm_constant_metanodes_from_nodes(nodes)


def kpm_metanodes_from_design_descr(
    design_descr: dict, specification: dict
) -> List[KPMDataflowMetanode]:
    """Generate a list of all metanodes based on values assigned to ip core
    ports and an 'external' section of Topwrap's design description
    """
    externals = kpm_external_metanodes_from_design_descr(design_descr)
    constants = kpm_constant_metanodes_from_design_descr(design_descr, specification)
    return list(externals + constants)


def _find_dataflow_metanode_by_external_name(
    metanodes: List[KPMDataflowMetanode], external_name: str
) -> Optional[KPMDataflowMetanode]:
    for metanode in metanodes:
        prop_val = get_metanode_property_value(metanode.to_json_format())
        if prop_val == external_name:
            return metanode
    logging.warning(f"External port/interface '{external_name}' not found in design description")


def _find_dataflow_metanode_by_constant_value(
    metanodes: List[KPMDataflowMetanode], value: int
) -> Optional[KPMDataflowNode]:
    for metanode in metanodes:
        prop_val = get_metanode_property_value(metanode.to_json_format())
        if prop_val == str(value):
            return metanode
    logging.warning(f"Constant value '{value}' not found in design description")


def kpm_metanodes_connections_from_design_descr(
    design_descr: dict, nodes: List[KPMDataflowNode], metanodes: List[KPMDataflowMetanode]
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
        if kpm_interface is None:
            raise Exception("Node interface was not found")

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


def create_subgraph_external_interfaces(
    subgraph_ports: dict,
) -> Tuple[List[KPMDataflowSubgraphnodeInterface], Dict[str, str]]:
    """Creates subgraph node interfaces based on node "external" field in Topwrap design description"""
    interfaces = []
    interface_map_updates = {}

    for direction, port_names in subgraph_ports.items():
        for port_name in port_names:
            new_interface = KPMDataflowSubgraphnodeInterface(port_name, direction)
            interface_map_updates[port_name] = new_interface.id
            interfaces.append(new_interface)

    return (interfaces, interface_map_updates)


def kpm_subgraph_nodes_from_design_descr(
    design_descr: dict,
) -> Tuple[List[KPMDataflowSubgraphnode], SubgraphMaps]:
    """Creates a list of subgraph nodes based on current hierarchy level in Topwrap design description."""
    # Uses two dictionaries in order to avoid time consuming searching in graphs

    if "hierarchies" not in design_descr["design"].keys():
        return ([], SubgraphMaps())

    subgraph_nodes = []
    submap_updates = SubgraphMaps()

    for subgraph_name, subgraph_data in design_descr["design"]["hierarchies"].items():
        interfaces, interface_map_updates = create_subgraph_external_interfaces(
            subgraph_data["external"]["ports"]
        )
        submap_updates.interface_name_id_map.update(interface_map_updates)

        subgraph_properties = []
        property_data = design_descr["design"].get("parameters", {}).get(subgraph_name, None)

        if property_data is not None:
            for property_name, property_value in property_data.items():
                subgraph_properties.append(KPMDataflowNodeProperty(property_name, property_value))

        subgraph_node = KPMDataflowSubgraphnode(
            subgraph_name, subgraph_properties, list(interfaces), IDGenerator().generate_id()
        )

        submap_updates.subgraph_name_id_map[subgraph_name] = subgraph_node.subgraph
        subgraph_nodes.append(subgraph_node)

    return (subgraph_nodes, submap_updates)


def _get_external_subgraph_connections(design_descr: dict) -> List[dict]:
    def _is_subgraph_reference(conn_descr: dict) -> bool:
        return isinstance(conn_descr["connection"], str)

    return list(filter(_is_subgraph_reference, _get_flattened_connections(design_descr)))


def _expose_external_subgraph_interfaces(
    subgraph_data: dict,
    subgraph_nodes: List[KPMDataflowNode],
    subgraph_interface_name_id_map: Dict[str, str],
) -> Dict[str, str]:
    """Creates "externalName" reference in subgraph node interface.
    Reference has to be to exactly one level higher to preserve hierarchy.
    Additionally changes the id to be the same as exposed interface"""
    interface_map_updates = {}
    _conns = _get_external_subgraph_connections(subgraph_data)
    for conn in _conns:
        conn_name = conn["connection"]

        kpm_subgraph_iface = _get_dataflow_interface_by_name(
            conn["port_iface_name"], conn["ip_name"], subgraph_nodes
        )
        if kpm_subgraph_iface is None:
            logging.warning(
                f"Not found interface with name {conn['port_iface_name']} and because of that can't expose this interface"
            )
            return interface_map_updates

        kpm_subgraph_iface.id = subgraph_interface_name_id_map[conn_name]
        kpm_subgraph_iface.external_name = conn_name
        interface_map_updates[kpm_subgraph_iface.name] = kpm_subgraph_iface.id

    return interface_map_updates


def create_subgraphs(
    design_subgraphs: dict,
    specification: dict,
    previous_nodes: list,
    ips: dict,
    subgraph_maps: SubgraphMaps,
) -> List[KPMDataflowGraph]:
    """Creates all subgraphs from Topwrap design hierarchy section."""
    if "hierarchies" not in design_subgraphs.keys():
        return []

    design_subgraphs = design_subgraphs["hierarchies"]
    subgraphs = []
    for subgraph_name, subgraph_data in design_subgraphs.items():
        core_nodes = kpm_nodes_from_design_descr(subgraph_data, specification, ips)
        current_subgraph_nodes, submaps_updates = kpm_subgraph_nodes_from_design_descr(
            subgraph_data
        )
        subgraph_maps.update_maps(submaps_updates)

        all_subgraph_nodes = core_nodes + current_subgraph_nodes

        subgraph_maps.interface_name_id_map.update(
            _expose_external_subgraph_interfaces(
                subgraph_data,
                all_subgraph_nodes + previous_nodes,
                subgraph_maps.interface_name_id_map,
            )
        )

        connections = kpm_connections_from_design_descr(subgraph_data, all_subgraph_nodes)

        subgraphs.append(
            KPMDataflowGraph(
                connections, all_subgraph_nodes, subgraph_maps.subgraph_name_id_map[subgraph_name]
            )
        )

        # Recursively do dfs adding each graph along the way.
        # That's why "ips" is required as an argument because each recursion step is passed design from current hierarchy
        subgraphs += create_subgraphs(
            subgraph_data["design"],
            specification,
            previous_nodes + all_subgraph_nodes,
            ips,
            subgraph_maps,
        )

    return subgraphs


def create_entry_graph(
    design_descr: dict, specification: dict
) -> Tuple[KPMDataflowGraph, SubgraphMaps]:
    """Creates entry graph for kpm design.
    Main difference between entry graph and other subgraphs is that the "external" field
    does not specify it's interfaces but external metanodes"""
    core_nodes = kpm_nodes_from_design_descr(design_descr, specification, design_descr["ips"])
    metanodes = kpm_metanodes_from_design_descr(design_descr, specification)

    subgraph_nodes, initial_subgraph_maps = kpm_subgraph_nodes_from_design_descr(design_descr)

    graph_nodes = core_nodes + subgraph_nodes

    connections = kpm_connections_from_design_descr(design_descr, graph_nodes)
    metanodes_connections = kpm_metanodes_connections_from_design_descr(
        design_descr, graph_nodes, metanodes
    )

    return (
        KPMDataflowGraph(connections + metanodes_connections, graph_nodes + metanodes),
        initial_subgraph_maps,
    )


def kpm_dataflow_from_design_descr(design_descr: dict, specification: dict) -> dict:
    """Generate Pipeline Manager dataflow from a design description
    in Topwrap's yaml format
    """

    entry_graph, initial_subgraph_maps = create_entry_graph(design_descr, specification)
    subgraphs = create_subgraphs(
        design_descr["design"],
        specification,
        entry_graph.nodes,
        design_descr["ips"],
        initial_subgraph_maps,
    )
    subgraphs.append(entry_graph)

    dataflow = {
        "graphs": [graph.to_json_format() for graph in subgraphs],
        "entryGraph": entry_graph.id,
        "version": "20240723.13",
    }

    return dataflow
