# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Dict, List, Optional

from pipeline_manager_backend_communication.misc_structures import MessageType

from topwrap.hdl_parsers_utils import (
    ParameterToEval,
    evaluate_parameter_list,
)

from .kpm_common import (
    InterfaceFromConnection,
    check_for_iface_in_conn_graph,
    find_connected_interfaces,
    find_dataflow_interface_by_id,
    get_all_graph_connections,
    get_all_graph_nodes,
    get_dataflow_constant_metanodes,
    get_dataflow_current_hierarchy_ip_nodes,
    get_dataflow_external_interfaces,
    get_dataflow_external_metanodes,
    get_dataflow_ips_interfaces,
    get_dataflow_subgraph_meta_interfaces,
    get_dataflow_subgraph_metanodes,
    get_dataflow_subgraph_nodes,
    get_exposed_subgraph_meta_iface,
    get_graph_id_from_node,
    get_graph_id_name,
    get_interfaces_from_connection,
    get_metanode_interface_id,
    get_metanode_property_value,
    is_metanode,
)
from .util import JsonType, UnreachableError


@dataclass
class CheckResult:
    """
    Return type of each validation check


    :param str check_name: Name of the check
    :param MessageType status: Check can be return one of three MessageTypes (OK, ERROR, WARNING)

        - OK - this status is set when check was successful
        - WARNING - check have failed but it is possible to represent the graph in design yaml
        - ERROR - it is not possible to represent graph in design yaml
    :param int error_count: Number of errors if status is not OK
    :param str | None message: Message describing errors
    """

    check_name: str
    status: MessageType
    error_count: int = 0
    message: Optional[str] = None


class DataflowValidator:
    """
    The main class that contains all the validation checks.
    The purpose of validation is to check for common errors the user may make while creating the
    design and make sure the design can be saved in topwrap yaml format.
    These functions are called in two cases:

    1) When there is a call from KPM for dataflow_validate (the user has clicked Validate in GUI)
    2) When a user tries to save the design
    """

    def __init__(self, dataflow: JsonType):
        """
        :param JsonType dataflow: Dataflow that will be checked
        """

        self.dataflow = dataflow

    def check_duplicate_node_names(self) -> CheckResult:
        """
        Check for any duplicate IP instance names in the graph (graph represents a hierarchy level).
        This check prevents from creating multiple nodes with the same "instanceName" in a given
        graph, since this is invalid in design.
        There can be multiple nodes with the same "instanceName" in the whole design (on various
        hierarchy levels).
        """

        check_name = "Duplicate IP names"

        all_duplicates = set()
        for graph in self.dataflow["graphs"]:
            names_set = set()
            duplicates = set()
            for node in graph["nodes"]:
                if not is_metanode(node):
                    graph_name = get_graph_id_name(self.dataflow, graph["id"]) or "Root graph"
                    node_graph_str = f"In {graph_name}: {node['instanceName']}"
                    if node_graph_str in names_set:
                        duplicates.add(node_graph_str)
                    else:
                        names_set.add(node_graph_str)
            all_duplicates.update(duplicates)

        if not all_duplicates:
            return CheckResult(check_name, MessageType.OK)
        err_msg = f"Duplicate block names: {str(list(all_duplicates))}"
        return CheckResult(check_name, MessageType.WARNING, len(all_duplicates), err_msg)

    def check_parameters_values(self) -> CheckResult:
        """
        Check if parameters in IP nodes are valid.

        This check ensures users are informed of any errors in parameter definitions.
        While it is possible to save the design with invalid parameters (e.g. save to YAML), such a
        design cannot be successfully built into Verilog because integer widths of all parameters
        must be determined during the build process.

        A parameter is considered valid if it meets any of the following conditions:

        - It is an instance of ``int``.
        - It has a correct value format, e.g.: ``16'h5A5A``.
        - It can be evaluated based on other parameters, e.g.:
            ``ADDR_WIDTH``: ``32``

            ``DATA_WIDTH``: ``ADDR_WIDTH/4`` (evaluates to 8, which is valid).
        """

        def _get_invalid_param_str(node_name: str, param_name: str, param_val: str):
            return f"{node_name}:{param_name} value: {param_val}"

        check_name = "Parameters values"
        parameter_list = []
        invalid_params_str = []

        # Only ip nodes have parameters
        for node in [
            *get_dataflow_current_hierarchy_ip_nodes(self.dataflow),
            *get_dataflow_subgraph_nodes(self.dataflow),
        ]:
            # Ignore identifier nodes, as they are supposed to have
            # string property values.
            # TODO: This should probably include more nodes?
            # (e.g. interconnects due to their manager/subordinate
            # parameters?)
            if node["name"] == "Identifier":
                continue

            for param in node.get("properties", []):
                parameter_list.append(
                    ParameterToEval(param["name"], param["value"], node["instanceName"])
                )

        evaluated_params = evaluate_parameter_list(parameter_list)

        for param in evaluated_params.not_evaluated:
            # Every kpm param that is not evaluated will be a str
            assert isinstance(param.value, str)
            invalid_params_str.append(f"{param.ip_core}:{param.name} value: {param.value}")

        # Check if constant metanodes have int value
        for node in get_dataflow_constant_metanodes(self.dataflow):
            name = node["properties"][0]["name"]
            value = node["properties"][0]["value"]

            try:
                int(value, base=0)
            except ValueError:
                invalid_params_str.append(f"Invalid constant in {name}:{value}")

        if invalid_params_str:
            err_msg = f"Invalid parameters values: {str(invalid_params_str)}"
            return CheckResult(check_name, MessageType.WARNING, len(invalid_params_str), err_msg)
        return CheckResult(check_name, MessageType.OK)

    def check_unconnected_ports_interfaces(self) -> CheckResult:
        """
        Check for unconnected ports or interfaces.
        This check helps identify any unconnected elements, warning the user about potential
        oversights or missed connections.
        """

        check_name = "Unconnected ports or interfaces"
        unconn_ifaces = set(
            [
                (node["instanceName"], interface["name"], interface["id"])
                for node in get_all_graph_nodes(self.dataflow)
                for interface in node["interfaces"]
            ]
        )

        # Extract all subgraph metanode interfaces
        exposed_subgraph_metanodes_interfaces = [
            (sub_metanode["instanceName"], get_exposed_subgraph_meta_iface(sub_metanode))
            for sub_metanode in get_dataflow_subgraph_metanodes(self.dataflow)
        ]
        metanodes_interfaces_data = [
            (metanode_name, metanode_iface["name"], metanode_iface["id"])
            for metanode_name, metanode_iface in exposed_subgraph_metanodes_interfaces
        ]

        # Remove externally referenced interfaces because they will always be unconnected
        for exposed_interface in metanodes_interfaces_data:
            unconn_ifaces.discard(exposed_interface)

        for conn in get_all_graph_connections(self.dataflow):
            iface_to = find_dataflow_interface_by_id(
                self.dataflow, InterfaceFromConnection(conn["to"], conn["id"])
            )
            if iface_to is None:
                raise ValueError(
                    f"Interface with id {conn['to']} in connection {conn['id']} cannot be found"
                )

            iface_from = find_dataflow_interface_by_id(
                self.dataflow, InterfaceFromConnection(conn["from"], conn["id"])
            )
            if iface_from is None:
                raise ValueError(
                    f"Interface with id {conn['from']} in connection {conn['id']} cannot be found"
                )

            unconn_ifaces.discard((iface_to.node_name, iface_to.iface_name, conn["to"]))
            unconn_ifaces.discard((iface_from.node_name, iface_from.iface_name, conn["from"]))

        if unconn_ifaces:
            unconn_ifaces_descrs = []
            for node_name, iface_name, _ in unconn_ifaces:
                unconn_ifaces_descrs.append(f"{iface_name} in {node_name}")
            return CheckResult(
                check_name,
                MessageType.WARNING,
                len(unconn_ifaces_descrs),
                f"Unconnected interfaces: {unconn_ifaces_descrs}",
            )
        return CheckResult(check_name, MessageType.OK)

    def check_external_in_to_external_out_connections(self) -> CheckResult:
        """
        Check for connections between two external metanodes.
        In our design format (YAML), connections to external nodes are always represented as
        `port: external`, regardless of whether the `external` node is an input or output.
        Therefore, connections directly between two external metanodes cannot be represented within
        this format and are invalid by design.
        """

        ext_ifaces_ids = get_dataflow_external_interfaces(self.dataflow).keys()
        check_name = "Connections between external sources"

        for conn in get_all_graph_connections(self.dataflow):
            if conn["from"] in ext_ifaces_ids and conn["to"] in ext_ifaces_ids:
                metanode_from, metanode_to = get_interfaces_from_connection(self.dataflow, conn)
                meta_from_name = getattr(metanode_from, "node_name", "metanode")
                meta_to_name = getattr(metanode_to, "node_name", "metanode")
                return CheckResult(
                    check_name,
                    MessageType.ERROR,
                    1,
                    f"Existing connection between external metanodes {meta_from_name} ->"
                    f" {meta_to_name}",
                )

        return CheckResult(check_name, MessageType.OK)

    def check_connection_to_subgraph_metanodes(self) -> CheckResult:
        """
        Check for any connections to exposed subgraph metanode ports.

        In this context:

        - **Exposed port**: A port on a subgraph metanode that represents the interface of the
            subgraph to the external graph. It is visible and accessible from outside the subgraph.
        - **Unexposed port**: An internal port on a subgraph metanode that is used for internal
            connections within the subgraph but is not accessible from the external graph.

        These metanodes are meant to represent ports of subgraph nodes.
        Connections to these metanodes should only occur via the unexposed ports.
        Any connection to an exposed port is considered an error because such connections cannot be
        represented in the design.
        """

        check_name = "Connections to exposed subgraph ports"
        for sub_metanode in get_dataflow_subgraph_metanodes(self.dataflow):
            sub_metanode_iface_id = get_exposed_subgraph_meta_iface(sub_metanode)["id"]
            graph_id = get_graph_id_from_node(self.dataflow, sub_metanode["id"])
            if check_for_iface_in_conn_graph(self.dataflow, sub_metanode_iface_id, graph_id):
                graph_name = get_graph_id_name(self.dataflow, graph_id)
                if graph_name is None:
                    return CheckResult(
                        check_name,
                        MessageType.ERROR,
                        1,
                        "Subgraph metanode cannot exist in root graph",
                    )
                return CheckResult(
                    check_name,
                    MessageType.ERROR,
                    1,
                    f"Connection to exposed port of subgraph metanode in {graph_name}",
                )
        return CheckResult(check_name, MessageType.OK)

    def check_duplicate_metanode_names(self) -> CheckResult:
        """
        Check for duplicate names of external metanodes.
        The name of metanode is in "External Name" property.
        In design, these external metanodes are referenced by this name so if there are multiple
        metanodes with the same name it will not be possible to represent them, hence the error.
        """

        check_name = "Duplicate names of external metanodes"
        ext_names_set = set()
        duplicates = set()

        for metanode in get_dataflow_external_metanodes(self.dataflow):
            external_name = get_metanode_property_value(metanode)
            # skip unnamed metanode case
            if not external_name:
                continue

            if external_name in ext_names_set:
                duplicates.add(external_name)
            else:
                ext_names_set.add(external_name)

        if duplicates:
            return CheckResult(
                check_name,
                MessageType.ERROR,
                len(duplicates),
                f"Duplicate external metanodes names: {str(list(duplicates))}",
            )
        return CheckResult(check_name, MessageType.OK)

    def check_unnamed_external_metanodes_with_multiple_conn(self) -> CheckResult:
        """
        Check for external metanodes that are connected to more than one port and don't have a
        user-specified name.
        This is important to check because it is an undefined behavior when saving a design.
        Currently, when there is a connection to an unnamed metanode in design this metanode will
        have the name of the port it's connected to.
        """

        err_ports = []
        check_name = "Unnamed metanodes with multiple connections"

        for metanode in get_dataflow_external_metanodes(self.dataflow):
            if get_metanode_property_value(metanode):
                continue

            conn_ifaces_ids = find_connected_interfaces(
                self.dataflow, get_metanode_interface_id(metanode)
            )
            if len(conn_ifaces_ids) > 1:
                for iface_conn in conn_ifaces_ids:
                    iface = find_dataflow_interface_by_id(self.dataflow, iface_conn)
                    if iface is None:
                        raise ValueError(
                            f"Interface {iface_conn.iface_id} is used in connection"
                            f" {iface_conn.connection_id} but is not defined"
                        )
                    err_ports.append(f"{iface.node_name}:{iface.iface_name}")

        if err_ports:
            return CheckResult(
                check_name,
                MessageType.ERROR,
                len(err_ports),
                f"External ports/interfaces {err_ports} are connected to "
                "`External Input` metanode with unspecified external name",
            )
        return CheckResult(check_name, MessageType.OK)

    def check_port_to_multiple_external_metanodes(self) -> CheckResult:
        """
        Check for ports that have connections to multiple external metanodes.
        Design schema allows only one connection between an IPcore/hierarchy port and an external
        metanode.
        The connection between the port and external metanode is a single entry, not a list that's
        why we can't add more connections.
        """

        check_name = "Ports with connections to multiple external metanodes"
        port_multiple_conn = []

        ext_ifaces_ids = get_dataflow_external_interfaces(self.dataflow).keys()

        for iface_id, iface in [
            *get_dataflow_ips_interfaces(self.dataflow).items(),
            *get_dataflow_subgraph_meta_interfaces(self.dataflow).items(),
        ]:
            # All connections where given iface id occurred
            iface_conns = [
                conn
                for conn in get_all_graph_connections(self.dataflow)
                if iface_id in conn.values()
            ]
            conn_to_external_metanode = False
            port_direction = None
            for conn in iface_conns:
                if conn_to_external_metanode:
                    # There can't be multiple interfaces in iface (ips can't have more than
                    # one since there isn't any external referencing and for subgraph metanodes
                    # we are collecting only theirs id's)
                    if len(iface) > 1:
                        raise UnreachableError

                    assert port_direction is not None, (
                        "Port direction can't be None due to underlying logic"
                    )
                    iface_data = find_dataflow_interface_by_id(
                        self.dataflow, InterfaceFromConnection(conn[port_direction], conn["id"])
                    )
                    if iface_data is None:
                        raise UnreachableError
                    port_multiple_conn.append(f"{iface_data.node_name}:{iface_data.iface_name}")
                    break

                if conn["from"] in ext_ifaces_ids:
                    port_direction = "to"
                elif conn["to"] in ext_ifaces_ids:
                    port_direction = "from"

                if port_direction is not None:
                    conn_to_external_metanode = True

        if port_multiple_conn:
            return CheckResult(
                check_name,
                MessageType.ERROR,
                len(port_multiple_conn),
                f"Ports connected to multiple external metanodes: {port_multiple_conn}",
            )
        return CheckResult(check_name, MessageType.OK)

    def validate_kpm_design(self) -> Dict[str, List[str]]:
        """
        Run checks to validate the user-created design in KPM.
        Checks are designed to inform the user about errors present in his design that make it
        impossible to save and display warnings about potential issues in the design.
        """
        checks = [
            self.check_duplicate_node_names,
            self.check_parameters_values,
            self.check_external_in_to_external_out_connections,
            self.check_port_to_multiple_external_metanodes,
            self.check_unnamed_external_metanodes_with_multiple_conn,
            self.check_duplicate_metanode_names,
            self.check_connection_to_subgraph_metanodes,
            self.check_unconnected_ports_interfaces,
        ]

        messages = {"errors": [], "warnings": []}
        for check in checks:
            check_result = check()
            if check_result.status == MessageType.ERROR:
                messages["errors"].append(check_result.message)
            elif check_result.status == MessageType.WARNING:
                messages["warnings"].append(check_result.message)

        return messages
