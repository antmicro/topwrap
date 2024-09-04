# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import logging
from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, List, Optional, Tuple, cast

from typing_extensions import override

from topwrap.hdl_parsers_utils import PortDirection
from topwrap.ip_desc import IPCoreParameter

from .design import DesignDescription, DesignExternalPorts, DesignSection
from .kpm_common import (
    CONST_NAME,
    EXPOSED_IFACE,
    EXT_INOUT_NAME,
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    SPECIFICATION_VERSION,
    SUBGRAPH_METANODE,
    get_metanode_property_value,
)


@dataclass
class SubgraphMaps:
    """Helper class for dicts that are used during subgraph creation"""

    interface_name_id_map: Dict[str, str] = field(default_factory=dict)
    subgraph_name_id_map: Dict[str, str] = field(default_factory=dict)

    def update_maps(self, submaps_update: "SubgraphMaps") -> None:
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

    def __init__(self, name: str, direction: str, value: Optional[int] = None):
        if direction not in self.kpm_direction_extensions_dict.values():
            raise ValueError(f"Invalid interface direction: {direction}")

        self.id = "ni_" + IDGenerator().generate_id()
        self.name = name
        self.direction = direction
        self.value = value
        self.external_name: Optional[str] = None

    def to_json_format(self):
        json_format = {
            "name": self.name,
            "id": self.id,
            "direction": self.direction,
            "side": ("left" if (self.direction == self.KPM_DIR_INPUT) else "right"),
        }
        if self.external_name is not None:
            json_format[EXPOSED_IFACE] = self.external_name
        return json_format


class KPMDataflowSubgraphnodeInterface(KPMDataflowNodeInterface):
    def __init__(self, name: str, direction: str):
        if direction not in KPMDataflowNodeInterface.kpm_direction_extensions_dict.keys():
            raise ValueError(f"Invalid subgraph direction: {direction}")
        super().__init__(name, KPMDataflowNodeInterface.kpm_direction_extensions_dict[direction])


class KPMDataflowMetanodeInterface(KPMDataflowNodeInterface):
    EXT_IFACE_NAME = "external"
    CONST_IFACE_NAME = "constant"
    SUB_IFACE_IN_NAME = "subgraph in"
    SUB_IFACE_OUT_NAME = "subgraph out"

    def __init__(self, name: str, direction: str, **kwargs: Any):
        meta_iface_names = [
            self.EXT_IFACE_NAME,
            self.CONST_IFACE_NAME,
            self.SUB_IFACE_IN_NAME,
            self.SUB_IFACE_OUT_NAME,
        ]
        if name not in meta_iface_names:
            raise ValueError(f"Invalid metanode interface name: {name}")

        super().__init__(name, direction, **kwargs)


class KPMDataflowNodeProperty:
    def __init__(self, name: str, value: IPCoreParameter):
        self.id = IDGenerator().generate_id()
        self.name = name
        self.value = value

    def to_json_format(self):
        return {"name": self.name, "id": self.id, "value": self.value}


class KPMDataflowMetanodeProperty(KPMDataflowNodeProperty):
    KPM_EXT_PROP_NAME = "External Name"
    KPM_CONST_VALUE_PROP_NAME = "Constant Value"

    def __init__(self, name: str, value: IPCoreParameter):
        if name not in [self.KPM_EXT_PROP_NAME, self.KPM_CONST_VALUE_PROP_NAME]:
            raise ValueError(f"Invalid metanode property name: {name}")

        super().__init__(name, value)


class KPMDataflowNode:
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
            "twoColumn": True,
            "interfaces": [interface.to_json_format() for interface in self.interfaces],
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
    def __init__(self, **kwargs: Any):
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


class KPMDataflowSubgraphMetanode(KPMDataflowMetanode):
    def __init__(self, port_name: str) -> None:
        super().__init__(
            name=port_name,
            type=SUBGRAPH_METANODE,
            properties=[],
            interfaces=[
                KPMDataflowMetanodeInterface(
                    KPMDataflowMetanodeInterface.SUB_IFACE_OUT_NAME,
                    KPMDataflowNodeInterface.KPM_DIR_OUTPUT,
                ),
                KPMDataflowMetanodeInterface(
                    KPMDataflowMetanodeInterface.SUB_IFACE_IN_NAME,
                    KPMDataflowNodeInterface.KPM_DIR_INPUT,
                ),
            ],
        )

    def get_unexposed_port_id(self) -> str:
        for idx, interface in enumerate(self.interfaces):
            if interface.external_name is not None:
                # Subgraph metanodes have two interfaces, we want to make connections to the interface that is not exposed
                # (idx + 1) % 2 will select interface that is not exposed
                return self.interfaces[(idx + 1) % 2].id
        raise ValueError("No interface is exposed in subgraph metanode")


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
        self,
        connections: List[KPMDataflowConnection],
        nodes: List[KPMDataflowNode],
        id: Optional[str] = None,
    ):
        self.connections = connections
        self.nodes = nodes
        self.id = id if id else IDGenerator().generate_id()

    def to_json_format(self) -> dict:
        return {
            "id": self.id,
            "nodes": [node.to_json_format() for node in self.nodes],
            "connections": [connection.to_json_format() for connection in self.connections],
        }


def _get_specification_node_by_type(type: str, specification: dict) -> Optional[dict]:
    """Return a node of type `type` from specification"""
    for node in specification["nodes"]:
        if type == node["layer"]:
            return node
    logging.warning(f'Node type "{type}" not found in specification')


def _ipcore_param_to_kpm_value(param: IPCoreParameter) -> str:
    """Return a string representing an IP core parameter,
    that will be placed in dataflow node property textbox
    """
    if isinstance(param, int):
        return str(param)
    if isinstance(param, str):
        return param
    else:
        width = str(param.width)
        value = hex(int(param.value))[2:]
        return width + "'h" + value


def get_kpm_nodes_from_design(
    design_descr: DesignDescription, specification: dict
) -> List[KPMDataflowNode]:
    """Return list of nodes that will be created based on design and specification from names list"""
    nodes = []
    design = design_descr.design
    parameters = design.parameters
    for ip_name in design_descr.ips:
        ports = design.ports.get(ip_name, {})
        ip_type = design_descr.ips[ip_name].path.stem
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
                    logging.warning(f"Parameter '{param_name}' not found in node {ip_name}")

        interfaces = []
        for interface in spec_node["interfaces"]:
            dir = interface["direction"]
            value = (
                None
                if ((dir != "input") or ("iface" in interface["type"][0]))
                else ports.get(interface["name"])
            )
            interfaces.append(KPMDataflowNodeInterface(interface["name"], dir, value))

        nodes.append(KPMDataflowNode(ip_name, ip_type, list(kpm_properties.values()), interfaces))
    return nodes


def kpm_nodes_from_design_descr(
    design_descr: DesignDescription, specification: dict
) -> List[KPMDataflowNode]:
    """Generate KPM dataflow nodes based on Topwrap's design
    description yaml (e.g. generated from YAML design description)
    and already loaded KPM specification.
    """

    design = design_descr.design
    interconnect_names = list(design.interconnects.keys())
    if interconnect_names:
        logging.warning(
            f"Imported design contains interconnects ({interconnect_names}) which are not "
            "supported yet. The imported design will be incomplete"
        )

    return get_kpm_nodes_from_design(design_descr, specification)


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


def _get_flattened_connections(design_descr: DesignDescription) -> List[dict]:
    """Helper function to get a list of flattened connections
    from a design description yaml.
    """

    conn_descrs = []
    design = design_descr.design

    for sec in (design.ports, design.interfaces):
        for ip_name in sec.keys():
            for port_iface_name, value in sec[ip_name].items():
                const_value = None
                if isinstance(value, int):
                    connection = CONST_NAME
                    const_value = value
                else:
                    connection = sec[ip_name][port_iface_name]

                conn_descr = {
                    "ip_name": ip_name,
                    "port_iface_name": port_iface_name,
                    "connection": connection,
                }
                if const_value is not None:
                    conn_descr["const_val"] = const_value
                conn_descrs.append(conn_descr)

    return conn_descrs


def _get_inout_connections(ports: DesignExternalPorts) -> List[dict]:
    """Return all inout connections from ports"""
    conn_descrs = []
    inouts = ports.inout

    for [ip_name, port_name] in inouts:
        conn_descrs.append(
            {"ip_name": ip_name, "port_iface_name": port_name, "connection": port_name}
        )
    return conn_descrs


def _get_external_connections(design_descr: DesignDescription) -> List[dict]:
    """Get connections to externals from 'ports' and 'interfaces'
    sections of design description.
    """
    ext_connections = list(
        filter(
            lambda conn_descr: isinstance(conn_descr["connection"], str),
            _get_flattened_connections(design_descr),
        )
    ) + _get_inout_connections(design_descr.external.ports)

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


def _get_ipcores_connections(design_descr: DesignDescription) -> List[dict]:
    """Get connections between IP cores from 'ports' and 'interfaces'
    sections of design description.
    """

    def _is_ipcore_connection(conn_descr: dict) -> bool:
        """Check if a connection is between two IP cores.
        If it's not a list then it is some external connection"""
        return isinstance(conn_descr["connection"], list) or isinstance(
            conn_descr["connection"], tuple
        )

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
    interface_input = KPMDataflowNodeInterface.KPM_DIR_INPUT
    interface_output = KPMDataflowNodeInterface.KPM_DIR_OUTPUT
    interface_inout = KPMDataflowNodeInterface.KPM_DIR_INOUT

    if dir_from == interface_input and dir_to in [interface_output, interface_inout]:
        # Don't show warnings for external metanodes because connection input -> output is legal there
        if kpm_iface_from.name != KPMDataflowMetanodeInterface.EXT_IFACE_NAME:
            logging.warning(
                "In connection: "
                f"'{kpm_iface_from.name}<->{kpm_iface_to.name}' "
                f"Input is connected to {dir_to}, connection will be automatically reversed to fix this issue"
            )
        return KPMDataflowConnection(kpm_iface_to.id, kpm_iface_from.id)

    if dir_from == dir_to and dir_from != interface_inout:
        logging.warning(
            "Port/interface direction mismatch for connection: "
            f"'{kpm_iface_from.name}<->{kpm_iface_to.name}'"
            f" {dir_from} is connected to {dir_to}"
        )
        return

    return KPMDataflowConnection(kpm_iface_from.id, kpm_iface_to.id)


def kpm_connections_from_design_descr(
    design_descr: DesignDescription,
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
    design_descr: DesignDescription,
) -> List[KPMDataflowExternalMetanode]:
    """Generate a list of external metanodes based on the contents of
    'external' section of Topwrap's design description
    """

    metanodes = []
    dir_to_metanode_type = {"in": EXT_INPUT_NAME, "out": EXT_OUTPUT_NAME, "inout": EXT_INOUT_NAME}

    for conn_group in (design_descr.external.ports, design_descr.external.interfaces):
        for dir, conns in conn_group.as_dict.items():
            for conn in conns:
                metanodes.append(
                    KPMDataflowExternalMetanode(
                        dir_to_metanode_type[dir.value], conn if isinstance(conn, str) else conn[1]
                    )
                )

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
    design_descr: DesignDescription, specification: dict
) -> List[KPMDataflowConstantMetanode]:
    """Generate a list of constant metanodes based on values assigned to ip core
    ports of Topwrap's design description
    """
    nodes = kpm_nodes_from_design_descr(design_descr, specification)
    return kpm_constant_metanodes_from_nodes(nodes)


def kpm_metanodes_from_design_descr(
    design_descr: DesignDescription, specification: dict
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
    design_descr: DesignDescription,
    nodes: List[KPMDataflowNode],
    metanodes: List[KPMDataflowMetanode],
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
            raise Exception(f"Node {ext_conn['ip_name']} interface was not found")

        if isinstance(kpm_interface.value, int):
            if kpm_interface.direction != KPMDataflowNodeInterface.KPM_DIR_INPUT:
                logging.warning("Cannot assign output port to constant value")
                continue

            kpm_metanode = _find_dataflow_metanode_by_constant_value(metanodes, kpm_interface.value)
        else:
            kpm_metanode = _find_dataflow_metanode_by_external_name(
                metanodes, ext_conn["external_name"]
            )

        if kpm_metanode is not None:
            # Metanodes have exactly 1 interface; hence we can take 0th index
            # of the `interfaces` array of a metanode to access the interface.
            result.append(_create_connection(kpm_metanode.interfaces[0], kpm_interface))
    return [conn for conn in result if conn is not None]


def create_subgraph_external_interfaces(
    subgraph_ports: DesignExternalPorts, subgraph_name: str
) -> Tuple[List[KPMDataflowSubgraphnodeInterface], Dict[str, str]]:
    """Creates subgraph node interfaces based on node "external" field in Topwrap design description"""
    interfaces = []
    interface_map_updates = {}

    for direction, port_names in subgraph_ports.as_dict.items():
        for port_name in port_names:
            if direction == PortDirection.INOUT:
                raise ValueError("External inout ports inside hierarchies are not yet supported")
            new_interface = KPMDataflowSubgraphnodeInterface(cast(str, port_name), direction.value)
            interface_map_updates[f"{subgraph_name} {port_name}"] = new_interface.id
            interfaces.append(new_interface)

    return (interfaces, interface_map_updates)


def kpm_subgraph_nodes_from_design_descr(
    design_descr: DesignDescription,
) -> Tuple[List[KPMDataflowSubgraphnode], SubgraphMaps]:
    """Creates a list of subgraph nodes based on current hierarchy level in Topwrap design description."""
    # Uses two dictionaries in order to avoid time consuming searching in graphs

    subgraph_nodes = []
    submap_updates = SubgraphMaps()

    for subgraph_name, subgraph_data in design_descr.design.hierarchies.items():
        interfaces, interface_map_updates = create_subgraph_external_interfaces(
            subgraph_data.external.ports, subgraph_name
        )
        submap_updates.interface_name_id_map.update(interface_map_updates)

        subgraph_properties = []
        property_data = design_descr.design.parameters.get(subgraph_name, None)

        if property_data is not None:
            for property_name, property_value in property_data.items():
                subgraph_properties.append(KPMDataflowNodeProperty(property_name, property_value))

        subgraph_node = KPMDataflowSubgraphnode(
            subgraph_name, subgraph_properties, list(interfaces), IDGenerator().generate_id()
        )

        submap_updates.subgraph_name_id_map[subgraph_name] = subgraph_node.subgraph
        subgraph_nodes.append(subgraph_node)

    return (subgraph_nodes, submap_updates)


def _get_external_subgraph_connections(design_descr: DesignDescription) -> List[dict]:
    def _is_subgraph_reference(conn_descr: dict) -> bool:
        return isinstance(conn_descr["connection"], str)

    return list(filter(_is_subgraph_reference, _get_flattened_connections(design_descr)))


def _expose_external_subgraph_interfaces(
    subgraph_data: DesignDescription,
    subgraph_name: str,
    interface_name_id_map: Dict[str, str],
) -> List[KPMDataflowSubgraphMetanode]:
    """Creates "externalName" reference in subgraph node interface.
    Reference has to be to exactly one level higher to preserve hierarchy.
    Additionally changes the id to be the same as exposed interface"""
    interface_metanodes = []
    sub_ports = subgraph_data.external.ports
    sub_inter = subgraph_data.external.interfaces
    input_names = sub_ports.input + sub_inter.input
    output_names = sub_ports.output + sub_inter.output

    for sub_external_interface in input_names + output_names:
        metanode_name = f"{subgraph_name} {sub_external_interface}"
        interface_metanode = KPMDataflowSubgraphMetanode(metanode_name)
        # in subgraph metanode at index 1 is input, at 0 is output
        iface_index = 1 if sub_external_interface in input_names else 0
        interface_metanode.interfaces[iface_index].id = interface_name_id_map[metanode_name]
        interface_metanode.interfaces[iface_index].external_name = sub_external_interface
        interface_metanodes.append(interface_metanode)
    return interface_metanodes


def _get_metanode_with_interface(
    iface_id: str, metanodes_list: List[KPMDataflowSubgraphMetanode]
) -> KPMDataflowSubgraphMetanode:
    for metanode in metanodes_list:
        for meta_iface in metanode.interfaces:
            if meta_iface.id == iface_id:
                return metanode
    raise ValueError(f"Interface with id {iface_id} was not found")


def subgraph_connections_to_metanodes(
    subgraph_data: DesignDescription,
    subgraph_nodes: List[KPMDataflowNode],
    subgraph_name: str,
    interface_name_id_map: Dict[str, str],
    interface_metanodes: List[KPMDataflowSubgraphMetanode],
) -> Tuple[List[KPMDataflowConnection], List[KPMDataflowConstantMetanode]]:
    _conns = _get_external_subgraph_connections(subgraph_data)
    result = []
    metanodes = []

    for conn in _conns:
        kpm_core_iface = _get_dataflow_interface_by_name(
            conn["port_iface_name"], conn["ip_name"], subgraph_nodes
        )
        if kpm_core_iface is None:
            raise Exception(f"Node {conn['ip_name']} interface was not found")

        conn_name = conn["connection"]
        meta_interface_id = None
        if conn_name == CONST_NAME:
            constant_metanode = KPMDataflowConstantMetanode(conn["const_val"])
            metanodes.append(constant_metanode)
            meta_interface_id = constant_metanode.interfaces[0].id
            result.append(KPMDataflowConnection(meta_interface_id, kpm_core_iface.id))
        else:
            metanode = _get_metanode_with_interface(
                interface_name_id_map[f"{subgraph_name} {conn['connection']}"],
                interface_metanodes,
            )
            meta_interface_id = metanode.get_unexposed_port_id()
            result.append(KPMDataflowConnection(kpm_core_iface.id, meta_interface_id))

    return result, metanodes


def create_subgraphs(
    design_section: DesignSection,
    specification: dict,
    previous_nodes: List[KPMDataflowNode],
    parent_subgraph_maps: SubgraphMaps,
) -> List[KPMDataflowGraph]:
    """Creates all subgraphs from Topwrap design hierarchy section."""

    design_subgraphs = design_section.hierarchies
    subgraphs = []
    for subgraph_name, subgraph_data in design_subgraphs.items():
        core_nodes = kpm_nodes_from_design_descr(subgraph_data, specification)
        current_subgraph_nodes, submaps_updates = kpm_subgraph_nodes_from_design_descr(
            subgraph_data
        )

        subgraph_maps = SubgraphMaps()
        subgraph_maps.update_maps(submaps_updates)

        all_subgraph_nodes = core_nodes + current_subgraph_nodes
        interface_metanodes = _expose_external_subgraph_interfaces(
            subgraph_data, subgraph_name, parent_subgraph_maps.interface_name_id_map
        )

        connections = kpm_connections_from_design_descr(subgraph_data, all_subgraph_nodes)

        meta_connections, constant_metanodes = subgraph_connections_to_metanodes(
            subgraph_data,
            all_subgraph_nodes,
            subgraph_name,
            parent_subgraph_maps.interface_name_id_map,
            interface_metanodes,
        )

        subgraphs.append(
            KPMDataflowGraph(
                connections + meta_connections,
                all_subgraph_nodes + constant_metanodes + interface_metanodes,
                parent_subgraph_maps.subgraph_name_id_map[subgraph_name],
            )
        )

        subgraphs += create_subgraphs(
            subgraph_data.design,
            specification,
            previous_nodes + all_subgraph_nodes,
            subgraph_maps,
        )

    return subgraphs


def create_entry_graph(
    design_descr: DesignDescription, specification: dict
) -> Tuple[KPMDataflowGraph, SubgraphMaps]:
    """Creates entry graph for kpm design.
    Main difference between entry graph and other subgraphs is that the "external" field
    does not specify it's interfaces but external metanodes"""
    core_nodes = kpm_nodes_from_design_descr(design_descr, specification)

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


def kpm_dataflow_from_design_descr(design_descr: DesignDescription, specification: dict) -> dict:
    """Generate Pipeline Manager dataflow from a design description
    in Topwrap's yaml format
    """

    entry_graph, initial_subgraph_maps = create_entry_graph(design_descr, specification)
    subgraphs = create_subgraphs(
        design_descr.design,
        specification,
        entry_graph.nodes,
        initial_subgraph_maps,
    )
    subgraphs.append(entry_graph)

    dataflow = {
        "graphs": [graph.to_json_format() for graph in subgraphs],
        "entryGraph": entry_graph.id,
        "version": SPECIFICATION_VERSION,
    }

    return dataflow
