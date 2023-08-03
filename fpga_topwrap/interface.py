# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from .parsers import parse_interface_definitions


class InterfaceDef:
    """This class represents an interface definition."""

    def __init__(self, name, prefix, signals):
        """
        :param name: full name of the interface
        :param prefix: prefix used as a short identifier for the interface
        :param signals: collection of names of required and optional signals
        :type signals: dict {'required': [str], 'optional': [str]}
        """
        self.name = name
        self.prefix = prefix
        self.signals = signals
        if "required" not in self.signals.keys():
            self.signals["required"] = list()
        if "optional" not in self.signals.keys():
            self.signals["optional"] = list()

    def __repr__(self):
        return f"Name: {self.name}, signals: {self.signals}"


# this holds all predefined interfaces
interface_definitions = [
    InterfaceDef(x["name"], x["port_prefix"], x["signals"]) for x in parse_interface_definitions()
]


def get_interface_by_name(name: str):
    """Retrieve a predefined interface definition by its name

    :return: `InterfaceDef` object, or `None` if there's no such interface
    """
    for definition in interface_definitions:
        if definition.name == name:
            return definition
    return None


def get_interface_by_prefix(prefix: str):
    """Retrieve a predefined interface definition by its prefix

    :return: `InterfaceDef` object, or `None` if there's no such interface
    """
    for definition in interface_definitions:
        if definition.prefix == prefix:
            return definition
    return None
