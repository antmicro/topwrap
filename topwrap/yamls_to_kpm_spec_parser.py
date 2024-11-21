# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Collection, Dict, List, Optional

from pipeline_manager.specification_builder import SpecificationBuilder

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import (
    KPMDataflowExternalMetanode,
    KPMDataflowMetanodeInterface,
    KPMDataflowNodeInterface,
)
from topwrap.ip_desc import (
    IPCoreComplexParameter,
    IPCoreDescription,
    IPCoreInterface,
    IPCoreParameter,
    IPCorePorts,
)
from topwrap.resource_field import FileHandler, ResourceReferenceHandler

from .interface import InterfaceMode
from .kpm_common import (
    CONST_NAME,
    METANODE_CATEGORY,
    SPECIFICATION_VERSION,
    SUBGRAPH_METANODE,
)
from .util import JsonType


@dataclass
class InterfaceType:
    name: str
    type: List[str]
    direction: str


@dataclass
class PropertyType:
    name: str
    type: str = "text"
    value: str = ""


class LayerType(Enum):
    IP_CORE = "IP Cores"
    EXTERNAL = "Externals"
    CONSTANT = "Constants"


@dataclass
class NodeType:
    name: str
    category: str
    layer: LayerType
    properties: List[PropertyType]
    interfaces: List[InterfaceType]
    additional_data: Optional[str] = None


@dataclass
class InterfaceStyle:
    iface_name: str
    color: str
    conn_color: str
    conn_pattern: str


def _ipcore_param_to_kpm_value(param: IPCoreParameter) -> str:
    """Returns a parameter default value, that will be displayed
    as an option in Pipeline Manager Node.

    :param param: may be int, str or {'value': ..., 'width': ... } dict.
    :return: in the dict case, the parameter will be shown in a Verilog
        hex format - e.g. {'value': 40, 'width': 16 } will be displayed
        as 16'h0028
    """
    if isinstance(param, str):
        return param
    elif isinstance(param, IPCoreComplexParameter):
        width = str(param.width)
        if isinstance(param.value, str) and "x" in param.value:
            value = param.value[2:]
        else:
            value = hex(int(param.value))[2:]
        return width + "'h" + value

    return str(param)


def _duplicate_ipcore_types_check(specification: JsonType):
    """Function to check for any duplicate node types in specification."""
    # If the name is already in types_set then it means that it's a duplicate
    types_set = set()
    duplicates = set()
    for node in specification["nodes"]:
        if node["name"] in types_set:
            duplicates.add(node["name"])
        else:
            types_set.add(node["name"])

    if len(duplicates) > 0:
        raise ValueError(f"Duplicate IP cores of types '{', '.join(duplicates)}'")


def _generate_ifaces_styling(interfaces_types: List[str]) -> List[InterfaceStyle]:
    """Generate interface styling definitions that style interfaces and their connections.

    :param interfaces_types: a list of interfaces types, e.g. ["iface_AXI4", "iface_AXILite"]

    :return: a list of type InterfaceStyle, which describes styling of all the interfaces"""
    COLOR_WHITE = "#ffffff"
    COLOR_GREEN = "#00ca7c"

    iface_styles = [
        InterfaceStyle(iface_type, COLOR_GREEN, COLOR_WHITE, "dashed")
        for iface_type in interfaces_types
    ]

    iface_styles.append(InterfaceStyle("port", COLOR_GREEN, COLOR_WHITE, "solid"))

    return iface_styles


def _get_ifaces_types(specification: JsonType) -> List[str]:
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


def _ipcore_params_to_prop_type(params: Dict[str, IPCoreParameter]) -> List[PropertyType]:
    """Returns a list of parameters in a format used in KPM specification."""
    prop_list = []
    for param_name, param_value in params.items():
        prop_list.append(PropertyType(param_name, "text", _ipcore_param_to_kpm_value(param_value)))
    return prop_list


def _ipcore_ports_to_iface_type(ports: IPCorePorts) -> List[InterfaceType]:
    """Returns lists of ports grouped by direction (inputs/outputs)
    in a format used in KPM specification."""
    return [
        InterfaceType(
            port.name,
            ["port"],
            KPMDataflowNodeInterface.kpm_direction_extensions_dict[port.direction.value],
        )
        for port in ports.flat
    ]


def _ipcore_ifaces_to_iface_type(ifaces: Dict[str, IPCoreInterface]) -> List[InterfaceType]:
    """Returns a list of interfaces grouped by direction (inputs/outputs)
    in a format used in KPM specification. Manager interfaces are considered
    outputs, subordinate interfaces are considered inputs and interfaces with
    unspecified direction are considered inouts."""

    iface_list = []
    for iface_name, iface_data in ifaces.items():
        if iface_data.mode in (InterfaceMode.SUBORDINATE, InterfaceMode.UNSPECIFIED):
            iface_list.append(
                InterfaceType(
                    iface_name,
                    [f"iface_{iface_data.type}"],
                    "input" if iface_data.mode == InterfaceMode.SUBORDINATE else "inout",
                )
            )
        else:
            iface_list.append(InterfaceType(iface_name, [f"iface_{iface_data.type}"], "output"))
    return iface_list


def create_core_node_from_yaml(res: ResourceReferenceHandler) -> NodeType:
    """Returns single KPM specification 'node' representing given IP core description YAML file"""
    ip_yaml = IPCoreDescription.load(res.to_path())

    ip_name = ip_yaml.name
    ip_props = _ipcore_params_to_prop_type(ip_yaml.parameters)
    ip_ports = _ipcore_ports_to_iface_type(ip_yaml.signals)
    ip_ifaces = _ipcore_ifaces_to_iface_type(ip_yaml.interfaces)

    return NodeType(
        ip_name, "IPcore", LayerType.IP_CORE, ip_props, ip_ports + ip_ifaces, res.to_str()
    )


def create_external_metanode(meta_name: str, interfaces_types: List[str]) -> NodeType:
    """Creates external metanode.
    :param meta_name: string representing which external metanode will it be. It has to be one of "External (Input, Output, Inout)"
    """
    if not KPMDataflowExternalMetanode.valid_node_name(meta_name):
        raise ValueError(f"Invalid external node name: {meta_name}")

    metanode_prop = PropertyType("External Name")
    metanode_iface = InterfaceType(
        KPMDataflowMetanodeInterface.EXT_IFACE_NAME,
        ["port"] + interfaces_types,
        KPMDataflowExternalMetanode.interface_dir_by_node_name[meta_name],
    )

    return NodeType(
        meta_name, METANODE_CATEGORY, LayerType.EXTERNAL, [metanode_prop], [metanode_iface]
    )


def create_constant_metanode(interfaces_types: List[str]) -> NodeType:
    """Creates constant metanode"""
    metanode_prop = PropertyType("Constant Value", "text", "0")
    metanode_iface = InterfaceType(
        KPMDataflowMetanodeInterface.CONST_IFACE_NAME, ["port"] + interfaces_types, "output"
    )

    return NodeType(
        CONST_NAME, METANODE_CATEGORY, LayerType.CONSTANT, [metanode_prop], [metanode_iface]
    )


def create_subgraph_metanode() -> NodeType:
    """Create subgraph metanode that is used as a representation of subgraph port"""
    sub_meta_in = InterfaceType(KPMDataflowMetanodeInterface.SUB_IFACE_OUT_NAME, ["port"], "output")
    sub_meta_out = InterfaceType(KPMDataflowMetanodeInterface.SUB_IFACE_IN_NAME, ["port"], "input")

    return NodeType(
        SUBGRAPH_METANODE, METANODE_CATEGORY, LayerType.EXTERNAL, [], [sub_meta_in, sub_meta_out]
    )


def add_node_type_to_specification(specification_builder: SpecificationBuilder, node: NodeType):
    """Adds all information from NodeType to specification_builder"""
    specification_builder.add_node_type(node.name, node.category, node.layer.value)

    for property in node.properties:
        specification_builder.add_node_type_property(
            node.name, property.name, property.type, property.value
        )

    for interface in node.interfaces:
        specification_builder.add_node_type_interface(
            node.name, interface.name, interface.type, interface.direction, maxcount=-1
        )

    if node.additional_data is not None:
        specification_builder.add_node_type_additional_data(node.name, node.additional_data)


def add_metadata_to_specification(
    specification_builder: SpecificationBuilder, interface_types: List[str]
):
    metadata = {
        "allowLoopbacks": True,
        "connectionStyle": "orthogonal",
        "movementStep": 15,
        "backgroundSize": 15,
        "layout": "CytoscapeEngine - grid",
        "twoColumn": True,
        "notifyWhenChanged": True,
        "layers": [{"name": lr.value, "nodeLayers": [lr.value]} for lr in LayerType],
        "navbarItems": [
            {
                "name": "Validate",
                "stopName": "Stop",
                "iconName": "Validate",
                "procedureName": "dataflow_validate",
                "allowToRunInParallelWith": ["dataflow_run", "custom_lint_files"],
            },
            {
                "name": "Run",
                "stopName": "Stop",
                "iconName": "Run",
                "procedureName": "dataflow_run",
                "allowToRunInParallelWith": ["dataflow_validate", "custom_lint_files"],
            },
        ],
    }
    for meta_name, meta_value in metadata.items():
        specification_builder.metadata_add_param(meta_name, meta_value)

    iface_styles = _generate_ifaces_styling(interface_types)
    for iface_style in iface_styles:
        specification_builder.metadata_add_interface_styling(
            iface_style.iface_name,
            iface_style.color,
            iface_style.conn_pattern,
            iface_style.conn_color,
        )


def generate_spec_using_builder(resources: Collection[ResourceReferenceHandler]) -> JsonType:
    """Build specification based on yamlfiles using SpecificationBuilder API"""
    specification_builder = SpecificationBuilder(spec_version=SPECIFICATION_VERSION)

    for res in resources:
        core_data = create_core_node_from_yaml(res)
        add_node_type_to_specification(specification_builder, core_data)

    interfaces_types = _get_ifaces_types(
        specification_builder._construct_specification(sort_spec=True)
    )
    interfaces_types.sort()

    for ext_name in KPMDataflowExternalMetanode.interface_dir_by_node_name.keys():
        ex_metanode = create_external_metanode(ext_name, interfaces_types)
        add_node_type_to_specification(specification_builder, ex_metanode)

    const_metanode = create_constant_metanode(interfaces_types)
    add_node_type_to_specification(specification_builder, const_metanode)

    subgraph_metanode = create_subgraph_metanode()
    add_node_type_to_specification(specification_builder, subgraph_metanode)

    add_metadata_to_specification(specification_builder, interfaces_types)

    return specification_builder._construct_specification(sort_spec=True)


def ipcore_yamls_to_kpm_spec(
    yamlfiles: Collection[Path], design: Optional[DesignDescription] = None
) -> JsonType:
    """Translate Topwrap's IP core description YAMLs into
    KPM specification 'nodes'.

    :param yamlfiles: IP core description YAMLs, that will be converted
    into KPM specification 'nodes'

    :param design: A DesignDescription with IP Core references that
    will get added to the generated specification

    :return: a dict containing KPM specification in which each 'node'
        represents a separate IP core
    """

    resources: set[ResourceReferenceHandler] = {FileHandler(path) for path in yamlfiles}
    paths = set(yamlfiles)
    if design is not None:
        for ip in design.all_ips:
            if ip.file.to_path() not in paths:
                paths.add(ip.file.to_path())
                resources.add(ip.file)

    specification = generate_spec_using_builder(resources)

    _duplicate_ipcore_types_check(specification)

    return specification
