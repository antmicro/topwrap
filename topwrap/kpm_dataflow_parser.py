# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

import marshmallow_dataclass
from typing_extensions import Self

from topwrap.common_serdes import MarshmallowDataclassExtensions, ext_field
from topwrap.design import (
    DesignDescription,
    DesignExternalSection,
    DS_InterfacesT,
    DS_PortsT,
)
from topwrap.design_to_kpm_dataflow_parser import KPMDataflowExternalMetanode
from topwrap.hdl_parsers_utils import PortDirection, parse_value_width_parameter
from topwrap.kpm_dataflow_validator import DataflowValidator

from .kpm_common import (
    EXT_INPUT_NAME,
    EXT_OUTPUT_NAME,
    InterfaceData,
    error_connections,
    find_connected_interfaces,
    find_dataflow_interface_by_id,
    find_dataflow_node_by_interface_name_id,
    get_all_graph_connections,
    get_all_graph_nodes,
    get_dataflow_constant_connections,
    get_dataflow_current_hierarchy_ip_nodes,
    get_entry_graph,
    get_exposed_subgraph_meta_iface,
    get_external_metanode_direction,
    get_interfaces_from_connection,
    get_metanode_interface_id,
    get_metanode_property_value,
    get_unexposed_subgraph_meta_iface,
    graph_to_isolated_dataflow,
    is_constant_metanode,
    is_external_metanode,
    is_kpm_interface_a_topwrap_interface,
    is_metanode,
    is_subgraph_metanode,
    is_subgraph_node,
    kpm_direction_to_port_dir,
)
from .util import JsonType, UnreachableError

logger = logging.getLogger(__name__)


class KPMExportException(Exception):
    """An exception thrown by KPM export handlers encountering a fatal error"""


@dataclass
class ConnectionData:
    iface_to: InterfaceData
    iface_from: InterfaceData
    node_to: JsonType
    node_from: JsonType


@marshmallow_dataclass.dataclass
class ExternalsAndConns(MarshmallowDataclassExtensions):
    external: DesignExternalSection = ext_field(DesignExternalSection)
    ports: DS_PortsT = ext_field(dict)
    interfaces: DS_InterfacesT = ext_field(dict)

    def add_external(
        self,
        intf: bool,
        dir: PortDirection,
        port_or_intf: Union[str, Tuple[str, str]],
        raise_on_dups: bool = True,
    ):
        if dir == PortDirection.INOUT and (isinstance(port_or_intf, str) or intf):
            raise UnreachableError  # arriving here can only be caused by our own logic fault
        coll = (self.external.interfaces.as_dict if intf else self.external.ports.as_dict)[dir]
        if port_or_intf not in coll:
            coll.append(port_or_intf)
        elif raise_on_dups:
            raise KPMExportException(
                f'{"Interface" if intf else "Port"} "{port_or_intf}" is duplicated'
            )

    def add_conn(
        self, intf: bool, node_name: str, port_name: str, target: Union[int, str, Tuple[str, str]]
    ):
        group = self.interfaces if intf else self.ports
        if intf and isinstance(target, int):
            raise KPMExportException("Tried assigning a constant value to a topwrap interface")
        if port_name in group.setdefault(node_name, {}):
            if not isinstance(target, tuple) or target[1] in group.setdefault(target[0], {}):
                raise KPMExportException(
                    f'Cannot represent connection "{node_name}.{port_name}" -> "{target}" as they are already connected to something else'
                )
            group[target[0]][target[1]] = (node_name, port_name)
        else:
            group[node_name][port_name] = target

    def merge_with(self, other: Self, raise_on_dups: bool = True):
        for is_intf, realm in (
            (True, other.external.interfaces.as_dict),
            (False, other.external.ports.as_dict),
        ):
            for dir, targets in realm.items():
                for target in targets:
                    self.add_external(is_intf, dir, target, raise_on_dups)

        for is_intf, realm in ((True, other.interfaces), (False, other.ports)):
            for ip_name, ports in realm.items():
                for port, target in ports.items():
                    self.add_conn(is_intf, ip_name, port, target)


def _kpm_properties_to_parameters(properties: List[JsonType]) -> JsonType:
    """Parse `properties` taken from a dataflow node into
    Topwrap's IP core's parameters.
    """
    result = dict()
    for property in properties:
        param_name = property["name"]
        param_val = property["value"]
        if re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
            result[param_name] = parse_value_width_parameter(param_val)
            continue

        try:
            result[param_name] = int(param_val, base=0)
        except ValueError:
            result[param_name] = param_val

    return result


def _kpm_nodes_to_parameters(dataflow_data: JsonType) -> JsonType:
    result = dict()
    for node in get_dataflow_current_hierarchy_ip_nodes(dataflow_data):
        result[node["instanceName"]] = _kpm_properties_to_parameters(node["properties"])
    return result


def _kpm_nodes_to_ips(dataflow_data: JsonType, specification: JsonType) -> JsonType:
    """Parse dataflow nodes into Topwrap's "ips" section
    of a design description yaml"""

    ips = {}
    filename = None
    instance_names = defaultdict(int)
    for node in get_dataflow_current_hierarchy_ip_nodes(dataflow_data):
        for spec_node in specification["nodes"]:
            if spec_node["name"] == node["name"]:
                if "additionalData" not in spec_node:
                    raise KPMExportException(
                        f'IP "{node["name"]}" does not contain the file path inside "additionalData"'
                    )
                filename = spec_node["additionalData"]
                break
        else:
            raise KPMExportException(f'IP "{node["name"]}" not found in the specification')

        cnt = instance_names[node["instanceName"]] = instance_names[node["instanceName"]] + 1
        if cnt > 1:
            node["instanceName"] += f"_{cnt}"
        ips[node["instanceName"]] = {
            "file": filename,
        }
    return ips


def _get_conn_ifaces_and_nodes(conn: JsonType, dataflow_data: JsonType) -> ConnectionData:
    iface_from, iface_to = get_interfaces_from_connection(dataflow_data, conn)
    if iface_to is None:
        raise error_connections(False, conn["to"])
    if iface_from is None:
        raise error_connections(False, conn["from"])

    node_to = find_dataflow_node_by_interface_name_id(
        dataflow_data, iface_to.iface_name, conn["to"]
    )
    if node_to is None:
        raise error_connections(True, conn["to"])

    node_from = find_dataflow_node_by_interface_name_id(
        dataflow_data, iface_from.iface_name, conn["from"]
    )
    if node_from is None:
        raise error_connections(True, conn["from"])

    return ConnectionData(iface_to, iface_from, node_to, node_from)


def _kpm_parse_connections_between_nodes(
    dataflow_data: JsonType, specification: JsonType
) -> ExternalsAndConns:
    """Parse dataflow connections between nodes representing IP cores and hierarchies"""

    data = ExternalsAndConns()

    for conn in get_all_graph_connections(dataflow_data):
        cd = _get_conn_ifaces_and_nodes(conn, dataflow_data)
        iface_to, iface_from, node_to, node_from = (
            cd.iface_to,
            cd.iface_from,
            cd.node_to,
            cd.node_from,
        )

        if is_metanode(node_from) or is_metanode(node_to):
            continue

        is_intf = is_kpm_interface_a_topwrap_interface(node_to, iface_to.iface_name, specification)
        data.add_conn(
            is_intf,
            iface_to.node_name,
            iface_to.iface_name,
            (iface_from.node_name, iface_from.iface_name),
        )

    return data


def _kpm_connections_to_constant(dataflow_data: JsonType) -> ExternalsAndConns:
    """Parse dataflow connections representing constant ports into design
    'ports' section of a Topwrap's design description yaml
    """
    data = ExternalsAndConns()

    for conn in get_dataflow_constant_connections(dataflow_data):
        conn_data = _get_conn_ifaces_and_nodes(conn, dataflow_data)
        ip_node = conn_data.node_to
        const_node = conn_data.node_from

        # Ensure the node is constant metanode
        if not is_constant_metanode(const_node):
            raise KPMExportException(
                "While parsing connections to constants, node_from was not a constant metanode"
            )

        iface_name = conn_data.iface_to.iface_name
        value = int(get_metanode_property_value(const_node))

        data.add_conn(False, ip_node["instanceName"], iface_name, value)

    return data


def _kpm_ext_handle_ext_meta(
    node: JsonType, dataflow: JsonType, specification: JsonType
) -> ExternalsAndConns:
    """Gather externals and their connections from an external metanode"""

    data = ExternalsAndConns()

    iname = get_metanode_property_value(node)
    dir = get_external_metanode_direction(node)
    id = get_metanode_interface_id(node)
    conns = [c for c in find_connected_interfaces(dataflow, id) if c.iface_id != id]
    if dir == PortDirection.INOUT:
        if len(conns) != 1:
            raise KPMExportException(
                "An inout port has an invalid amount of connections. Only 1 is supported by the schema"
            )
        if iname:
            logger.warning(
                f'An inout port has a custom name: "{iname}". This is meaningless and will not be preserved'
            )
    if len(conns) == 0:
        if not iname:
            logger.warning(
                "An external metanode without an external name that isn't connected to anything is meaningless and will not be preserved"
            )
            return data

        data.add_external(False, dir, iname)

    for conn in conns:
        to_intf = find_dataflow_interface_by_id(dataflow, conn)
        if to_intf is None:
            raise KPMExportException(
                f"External metanode connection target interface with id {conn.iface_id} was not found"
            )

        ip_node = find_dataflow_node_by_interface_name_id(
            dataflow, to_intf.iface_name, conn.iface_id
        )
        if ip_node is None:
            raise UnreachableError

        iface_name = to_intf.iface_name
        if not iname:
            iname = iface_name

        if dir == PortDirection.INOUT:
            data.add_external(False, dir, (ip_node["instanceName"], iname), raise_on_dups=False)
        else:
            is_intf = is_kpm_interface_a_topwrap_interface(ip_node, iface_name, specification)
            data.add_external(is_intf, dir, iname, raise_on_dups=False)
            data.add_conn(is_intf, ip_node["instanceName"], iface_name, iname)

    return data


def _kpm_ext_handle_subgraph_meta(
    node: JsonType, dataflow: JsonType, spec: JsonType
) -> ExternalsAndConns:
    """Gather externals and their connections from a subgraph metanode"""

    unexposed_iface = get_unexposed_subgraph_meta_iface(node)
    exposed_iface = get_exposed_subgraph_meta_iface(node)

    # transform the subgraph metanode into a regular
    # external metanode and handle it like one
    dir = kpm_direction_to_port_dir(exposed_iface["direction"])
    meta = KPMDataflowExternalMetanode(
        EXT_INPUT_NAME if dir == PortDirection.IN else EXT_OUTPUT_NAME,
        exposed_iface["externalName"],
    ).to_json_format()
    meta["interfaces"] = [unexposed_iface]

    return _kpm_ext_handle_ext_meta(meta, dataflow, spec)


def _kpm_ext_handle_legacy_exposed(node: JsonType, spec: JsonType) -> ExternalsAndConns:
    """Gather externals and their connections from 'exposed' ports on IP cores or subgraphs"""

    data = ExternalsAndConns()

    for interface in node["interfaces"]:
        if "externalName" in interface:
            dir = kpm_direction_to_port_dir(interface["direction"])
            if dir == PortDirection.INOUT:
                data.add_external(False, dir, (node["instanceName"], interface["externalName"]))
            else:
                is_intf = is_kpm_interface_a_topwrap_interface(node, interface["name"], spec)
                data.add_external(is_intf, dir, interface["externalName"])
                data.add_conn(
                    is_intf, node["instanceName"], interface["name"], interface["externalName"]
                )

    return data


def _kpm_gather_all_graph_externals(dataflow: JsonType, spec: JsonType) -> ExternalsAndConns:
    data = ExternalsAndConns()

    for node in get_all_graph_nodes(dataflow):
        if is_subgraph_metanode(node):
            data.merge_with(_kpm_ext_handle_subgraph_meta(node, dataflow, spec))
        elif is_external_metanode(node):
            data.merge_with(_kpm_ext_handle_ext_meta(node, dataflow, spec))
        elif not is_metanode(node):
            data.merge_with(_kpm_ext_handle_legacy_exposed(node, spec))

    return data


def kpm_dataflow_to_design(dataflow_data: JsonType, specification: JsonType) -> DesignDescription:
    validation_result = DataflowValidator(dataflow_data).validate_kpm_design()
    if validation_result["errors"]:
        raise KPMExportException(
            f"There are validation errors in the design which makes it impossible to save. Errors: {validation_result['errors']}"
        )

    def _inner(graph_id: str, name: str, is_top: bool = False) -> Dict[str, Any]:
        try:
            df = graph_to_isolated_dataflow(dataflow_data, graph_id)
            ips = _kpm_nodes_to_ips(df, specification)
            exts_and_conns = _kpm_gather_all_graph_externals(df, specification)

            exts_and_conns.merge_with(_kpm_connections_to_constant(df))
            exts_and_conns.merge_with(_kpm_parse_connections_between_nodes(df, specification))

            if not is_top and len(exts_and_conns.external.ports.inout) > 0:
                raise KPMExportException("Inouts inside hierarchies are not yet supported")

            return {
                "ips": ips,
                "external": exts_and_conns.external.to_dict(),
                "design": {
                    "ports": exts_and_conns.ports,
                    "interfaces": exts_and_conns.interfaces,
                    "parameters": _kpm_nodes_to_parameters(df),
                    "hierarchies": {
                        node["instanceName"]: _inner(node["subgraph"], node["instanceName"])
                        for node in get_all_graph_nodes(df)
                        if is_subgraph_node(node)
                    },
                },
            }
        except Exception as exc:
            raise KPMExportException(
                f'While parsing {"the top level" if is_top else f"hierarchy {name}"}, an exception occurred'
            ) from exc

    return DesignDescription.from_dict(_inner(get_entry_graph(dataflow_data)["id"], "top", True))
