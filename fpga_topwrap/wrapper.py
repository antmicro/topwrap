# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0

from typing import List

from amaranth import *

from .amaranth_helpers import WrapperPort


class Wrapper(Elaboratable):
    """Base class for modules that want to connect to each other.

    Derived classes must implement get_ports method that returns
    a list of WrapperPort's - external ports of a class that can
    be used as endpoints for connections.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def get_ports(self) -> List[WrapperPort]:
        """Return a list of external ports."""
        raise NotImplementedError('Derived classes must implement "get_ports" method')

    def get_port_by_name(self, name: str) -> WrapperPort:
        """Given port's name, return the port as WrapperPort object.

        :raises ValueError: If such port doesn't exist.
        """
        try:
            port = {signal.name: signal for signal in self.get_ports()}[name]
        except KeyError:
            raise ValueError(f"Port named '{name}' couldn't be found in the hierarchy: {self.name}")
        return port

    def get_ports_of_interface(self, iface_name: str) -> List[WrapperPort]:
        """Return a list of ports of specific interface.

        :raises ValueError: if such interface doesn't exist.
        """
        ports = [
            port for port in filter(lambda x: x.interface_name == iface_name, self.get_ports())
        ]
        if not ports:
            raise ValueError(f"No ports could be found for this interface name: {iface_name}")
        return ports
