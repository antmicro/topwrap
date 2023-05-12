# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
from typing import List
from enum import Enum


class DesignIP:
    def __init__(self,
                 name: str,
                 descr_file: str,
                 module: str,
                 parameters: dict):

        self.name = name
        self.descr_file = descr_file
        self.module = module
        self.parameters = parameters


class Direction(Enum):
    IN = 0,
    OUT = 1,
    INOUT = 2


class Port:
    def __init__(self, name: str, ip_name: str, dir: Direction):
        self.name = name
        self.ip_name = ip_name
        self.dir = dir


class PortConnection:
    """ Connection between two ports. An incoming connection can be from
    another port or may be fixed integer value.
    """

    def __init__(self, port_from: Port, port_to: Port, value: int = None):
        assert ((port_from is None) + (value is None) == 1)
        self.port_from = port_from
        self.port_to = port_to
        self.default = value


class Interface:
    def __init__(self, name: str, ip_name: str, dir: Direction, type: str):
        self.name = name
        self.ip_name = ip_name
        self.dir = dir
        self.type = type


class InterfaceConnection:
    def __init__(self, interface_from: Interface, interface_to: Interface):
        self.interface_from = interface_from
        self.interface_to = interface_to


class DesignDescription:
    def __init__(self,
                 ips: List[DesignIP],
                 ports_conn: List[PortConnection],
                 interfaces_conn: List[InterfaceConnection],
                 external: List[Port|Interface]):

        self.ips = ips
        self.ports_conn = ports_conn
        self.interfaces_conn = interfaces_conn
        self.external = external
