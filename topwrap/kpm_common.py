# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


CONST_NAME = "Constant"
EXT_INPUT_NAME = "External Input"
EXT_OUTPUT_NAME = "External Output"
EXT_INOUT_NAME = "External Inout"


def str_to_int(string: str) -> int:
    """Convert string to integer value while taking base prefix into account:
    - '0b', '0B' - convert to binary,
    - '0x', '0X' - convert to hexadecimal,
    - '0o', '0O', '0' - convert to octal,
    - others - convert to decimal.
    Returns 'None' if conversion is not possible, otherwise returns converted
    integer value.
    """
    conversion_dict = {
        "0b": 2,
        "0B": 2,
        "0x": 16,
        "0X": 16,
        "0O": 8,
        "0o": 8,
        "0": 8,
    }

    if isinstance(string, int):
        return string

    try:
        return int(string)
    except ValueError:
        pass

    for str, base in conversion_dict.items():
        if string.startswith(str):
            try:
                return int(string, base)
            except ValueError:
                return None

    return None


def is_external_metanode(node: dict) -> bool:
    """Return True if a node is an external metanode, False elsewhere."""
    return node["name"] in [EXT_INPUT_NAME, EXT_OUTPUT_NAME, EXT_INOUT_NAME]


def is_constant_metanode(node: dict) -> bool:
    """Return True if a node is a constant metanode, False elsewhere."""
    return node["name"] == CONST_NAME


def is_metanode(node: dict) -> bool:
    """Return True if a node is a metanode, False otherwise."""
    return is_external_metanode(node) or is_constant_metanode(node)


def get_dataflow_ip_nodes(dataflow_json) -> list:
    """Return a list of nodes which represent ip cores
    (i.e. filter out External Outputs, Inputs and Inouts)
    """
    return [node for node in dataflow_json["graph"]["nodes"] if not is_metanode(node)]


def get_dataflow_external_metanodes(dataflow_json) -> list:
    """Return a list of external metanodes (i.e. External Outputs and Inputs)"""
    return [node for node in dataflow_json["graph"]["nodes"] if is_external_metanode(node)]


def get_dataflow_constant_metanodes(dataflow_json) -> list:
    """Return a list of constant metanodes"""
    return [node for node in dataflow_json["graph"]["nodes"] if is_constant_metanode(node)]


def _get_interfaces(nodes: list) -> dict:
    """Return a dict of all the interfaces belonging to given nodes.
    The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    result = {}
    for node in nodes:
        for interface in node["interfaces"]:
            result[interface["id"]] = {
                "node_name": node["instanceName"],
                "iface_name": interface["name"],
                "iface_dir": interface["direction"],
            }
    return result


def get_dataflow_ips_interfaces(dataflow_json) -> dict:
    """Return a dict of all the interfaces of all the nodes representing
    ip cores. The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    return _get_interfaces(get_dataflow_ip_nodes(dataflow_json))


def get_dataflow_ip_connections(dataflow_json) -> list:
    """Return connections between two IP cores
    (e.g. filter out connections to external metanodes)
    """
    ifaces_ids = get_dataflow_ips_interfaces(dataflow_json).keys()
    return [
        conn
        for conn in dataflow_json["graph"]["connections"]
        if conn["from"] in ifaces_ids and conn["to"] in ifaces_ids
    ]


def get_dataflow_external_interfaces(dataflow_json) -> dict:
    """Return a dict of all the interfaces of all the external metanodes.
    The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    return _get_interfaces(get_dataflow_external_metanodes(dataflow_json))


def get_dataflow_constant_interfaces(dataflow_json) -> dict:
    """Return a dict of all the interfaces of all the constant metanodes.
    The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    return _get_interfaces(get_dataflow_constant_metanodes(dataflow_json))


def get_dataflow_external_connections(dataflow_json) -> list:
    """Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_external_interfaces(dataflow_json).keys()
    return [
        conn
        for conn in dataflow_json["graph"]["connections"]
        if conn["from"] in ifaces_ids or conn["to"] in ifaces_ids
    ]


def get_dataflow_constant_connections(dataflow_json) -> list:
    """Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_constant_interfaces(dataflow_json).keys()
    return [
        conn
        for conn in dataflow_json["graph"]["connections"]
        if conn["from"] in ifaces_ids or conn["to"] in ifaces_ids
    ]


def get_metanode_interface_id(metanode: dict) -> str:
    """Return given metanode's interface id. Metanodes always have exactly 1
    interface, so it suffices to take 0th element of the "interfaces" array.
    """
    return metanode["interfaces"][0]["id"]


def get_metanode_property_value(metanode: dict) -> str:
    """Return a value stored in an external metanode textbox.
    Metanodes always have exactly one property, so it suffices to take
    0th element of the "properties" array.
    """
    return metanode["properties"][0]["value"]


def find_dataflow_node_by_interface_id(dataflow_json, iface_id: str) -> dict:
    """Return dataflow node which has an `iface_id` interface"""
    for node in dataflow_json["graph"]["nodes"]:
        for interface in node["interfaces"]:
            if interface["id"] == iface_id:
                return node


def find_dataflow_interface_by_id(dataflow_json, iface_id: str) -> dict:
    """Return a dict {"node_name": ..., "iface_name": ..., "iface_dir": ...}
    that corresponds to a given 'iface_id'
    """
    interfaces = _get_interfaces(dataflow_json["graph"]["nodes"])
    if iface_id in interfaces.keys():
        return interfaces[iface_id]


def find_spec_interface_by_name(specification, node_type: str, iface_name: str) -> dict:
    """Find `name` interface of `ip_type` IP core in `specification`"""
    for node in specification["nodes"]:
        if node["layer"] != node_type:
            continue
        for interface in node["interfaces"]:
            if interface["name"] == iface_name:
                return interface


def find_dataflow_node_type_by_name(dataflow_data, node_name: str) -> str:
    for node in dataflow_data["graph"]["nodes"]:
        if node["instanceName"] == node_name:
            return node["name"]


def find_connected_interfaces(dataflow_json, iface_id: str) -> list:
    """Return an id list of all the interfaces connected to the interface
    with id equal to `iface_id`
    """
    result = []
    for conn in dataflow_json["graph"]["connections"]:
        if conn["from"] == iface_id:
            result.append(conn["to"])
        elif conn["to"] == iface_id:
            result.append(conn["from"])
    return result
