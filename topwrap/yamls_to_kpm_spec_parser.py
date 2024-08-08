# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import dataclass
from pathlib import PurePath
from typing import Dict, List, Optional, Union

from pipeline_manager.specification_builder import SpecificationBuilder

from topwrap.design_to_kpm_dataflow_parser import (
    KPMDataflowExternalMetanode,
    KPMDataflowNodeInterface,
)
from topwrap.ip_desc import (
    IPCoreDescription,
    IPCoreInterface,
    IPCoreParameter,
    IPCorePorts,
)

from .interface import InterfaceMode
from .kpm_common import CONST_NAME


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


@dataclass
class NodeType:
    name: str
    category: str
    layer: str
    properties: List[PropertyType]
    interfaces: List[InterfaceType]
    additional_data: Optional[str] = None


@dataclass
class InterfaceStyle:
    iface_name: str
    color: str
    conn_color: str
    conn_pattern: str


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
    elif isinstance(param, IPCoreParameter):
        width = str(param.width)
        value = hex(int(param.value))[2:]
        return width + "'h" + value

    return str(param)


def _duplicate_ipcore_types_check(specification: dict):
    """Function to check for any duplicate node types in specification."""
    # If the layer is already in types_set then it means that it's a duplicate
    types_set = set()
    duplicates = set()
    for node in specification["nodes"]:
        if node["layer"] in types_set:
            duplicates.add(node["layer"])
        else:
            types_set.add(node["layer"])
    for dup in list(duplicates):
        logging.warning(f"Multiple IP cores of type '{dup}'")


def _generate_ifaces_styling(interfaces_types: List[str]) -> List[InterfaceStyle]:
    """Generate interface styling definitinos that style interfaces and their connections.

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


def _get_ifaces_types(specification: dict) -> List[str]:
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


def _ipcore_params_to_prop_type(
    params: Dict[str, Union[int, str, IPCoreParameter]]
) -> List[PropertyType]:
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
    in a format used in KPM specification. Master interfaces are considered
    outputs, slave interfaces are considered inputs and interfaces with
    unspecified direction are considered inouts."""

    iface_list = []
    for iface_name, iface_data in ifaces.items():
        if iface_data.mode in (InterfaceMode.SLAVE, InterfaceMode.UNSPECIFIED):
            iface_list.append(
                InterfaceType(
                    iface_name,
                    [f"iface_{iface_data.type}"],
                    "input" if iface_data.mode == InterfaceMode.SLAVE else "inout",
                )
            )
        else:
            iface_list.append(InterfaceType(iface_name, [f"iface_{iface_data.type}"], "output"))
    return iface_list


def create_core_node_from_yaml(yamlfile: str) -> NodeType:
    """Returns single KPM specification 'node' representing given IP core description YAML file"""
    ip_yaml = IPCoreDescription.load(yamlfile)

    ip_name = PurePath(yamlfile).stem
    ip_props = _ipcore_params_to_prop_type(ip_yaml.parameters)
    ip_ports = _ipcore_ports_to_iface_type(ip_yaml.signals)
    ip_ifaces = _ipcore_ifaces_to_iface_type(ip_yaml.interfaces)

    return NodeType(ip_name, "IPcore", ip_name, ip_props, ip_ports + ip_ifaces, yamlfile)


def create_external_metanode(meta_name: str, interfaces_types: list) -> NodeType:
    """Creates external metanode.
    :param meta_name: string representing which external metanode will it be. It has to be one of "External (Input, Output, Inout)"
    """
    if not KPMDataflowExternalMetanode.valid_node_name(meta_name):
        raise ValueError(f"Invalid external node name: {meta_name}")

    metanode_prop = PropertyType("External Name")
    metanode_iface = InterfaceType(
        "external",
        ["port"] + interfaces_types,
        KPMDataflowExternalMetanode.interface_dir_by_node_name[meta_name],
    )

    return NodeType(meta_name, "Metanode", meta_name, [metanode_prop], [metanode_iface])


def create_constantant_metanode(interfaces_types: List[str]) -> NodeType:
    """Creates constant metanode"""
    metanode_prop = PropertyType("Constant Value", "text", "0")
    metanode_iface = InterfaceType("constant", ["port"] + interfaces_types, "output")

    return NodeType(CONST_NAME, "Metanode", CONST_NAME, [metanode_prop], [metanode_iface])


def add_node_type_to_specfication(specification_builder: SpecificationBuilder, node: NodeType):
    """Adds all information from NodeType to specification_builder"""
    specification_builder.add_node_type(node.name, node.category, node.layer)

    for property in node.properties:
        specification_builder.add_node_type_property(
            node.name, property.name, property.type, property.value
        )

    for interface in node.interfaces:
        specification_builder.add_node_type_interface(
            node.name, interface.name, interface.type, interface.direction
        )

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


def new_spec_builder(yamlfiles: List[str]) -> dict:
    """Build specification based on yamlfiles using SpecificationBuilder API"""
    SPECIFICATION_VERSION = "20240723.13"
    specification_builder = SpecificationBuilder(spec_version=SPECIFICATION_VERSION)

    for yamlfile in yamlfiles:
        core_data = create_core_node_from_yaml(yamlfile)
        add_node_type_to_specfication(specification_builder, core_data)

    interfaces_types = _get_ifaces_types(
        specification_builder._construct_specification(sort_spec=False)
    )

    for ext_name in KPMDataflowExternalMetanode.interface_dir_by_node_name.keys():
        ex_metanode = create_external_metanode(ext_name, interfaces_types)
        add_node_type_to_specfication(specification_builder, ex_metanode)

    const_metanode = create_constantant_metanode(interfaces_types)
    add_node_type_to_specfication(specification_builder, const_metanode)

    add_metadata_to_specification(specification_builder, interfaces_types)

    # TODO: Switch to using SpecificationBuilder.create_and_validate_spec() once the library is fixed.
    # specification = specification_builder.create_and_validate_spec(
    #     workspacedir=Path("../../build/workspace")
    # )

    return specification_builder._construct_specification(sort_spec=False)


def ipcore_yamls_to_kpm_spec(yamlfiles: List[str]) -> dict:
    """Translate Topwrap's IP core description YAMLs into
    KPM specification 'nodes'.

    :param yamlfiles: IP core description YAMLs, that will be converted
    into KPM specification 'nodes'

    :return: a dict containing KPM specification in which each 'node'
        represents a separate IP core
    """

    specification = new_spec_builder(yamlfiles)

    _duplicate_ipcore_types_check(specification)

    return specification
