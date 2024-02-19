# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pytest import raises

from topwrap.interface import (
    get_interface_by_name,
    get_interface_by_prefix,
    interface_definitions,
)


def match_interface(ports_matches):
    """
    :param ports_matches: a list of pairs (port_name, signal_name), where
    signal_name is compatible with interface definition.
    The list must belong to a single instance of the interface
    :return: interface name if the list matches an interface correctly
    """

    g_prefix = ports_matches[0][1].split("_")[0]
    g_instance = ports_matches[0][1].split("_")[1]
    iface = get_interface_by_prefix(g_prefix)

    for _, signal_name in ports_matches:
        prefix = signal_name.split("_")[0]
        instance = signal_name.split("_")[1]
        signal = signal_name.split("_")[2]

        # every port must belong to the same interface
        if prefix != iface.prefix:
            raise ValueError(
                f"signal prefix: {prefix} does not match"
                f"the prefix of this interface: {iface.prefix}"
            )
        # every port must belong to the same instance
        if instance != g_instance:
            raise ValueError(
                f"interface instance number: {instance} "
                "does not match with other ports of "
                f"this interface : {g_instance}"
            )

        if signal not in iface.signals["required"] + iface.signals["optional"]:
            raise ValueError(
                f"signal name: {signal_name} does not match any "
                f"signal in interface definition: {iface.name}"
            )

    return {"name": iface.name, "ports": ports_matches}


class TestInterfaceDef:
    def test_interfaces_presence(self):
        from topwrap import parsers as p

        interfaces = p.parse_interface_definitions()
        # parser returns non-empty list
        assert interfaces

    def test_predefined(self):
        assert interface_definitions, "No predefined interfaces " "could be retrieved"

    def test_iface_retrieve_by_name(self):
        name = "AXI4Stream"
        assert get_interface_by_name(name)

    def test_iface_retrieve_by_name_negative(self):
        name = "zxcvbnm"
        assert get_interface_by_name(name) is None

    def test_iface_retrieve_by_prefix(self):
        prefix = "AXIS"
        assert get_interface_by_prefix(prefix)

    def test_iface_retrieve_by_prefix_negative(self):
        prefix = "zxcvbnm"
        assert interface.get_interface_by_prefix(prefix) is None
