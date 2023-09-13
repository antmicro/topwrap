# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0

from typing import List

from .amaranth_helpers import WrapperPort


class HierarchyWrapper:
    """This class is a wrapper for hierarchies - in fact it is IPConnect to IPWrapper adapter.

    On one hand, the hierarchies are created with IPConnect class since they are a group of IP cores
    (or nested hierarchies) connected together.
    But on the other hand there must be an ability to put an existing hierarchy into a higher-level
    one - this is achieved by wrapping IPConnect with HierarchyWrapper.
    """

    def __init__(self, name: str, ipc) -> None:
        self.name = name
        self.ipc = ipc
        self._ports = []
        self._create_ports()

    def _create_ports(self):
        self._ports = self.ipc.get_ports()
        for ext_port in self._ports:
            setattr(self, ext_port.name, ext_port)

    def get_port_by_name(self, name: str) -> WrapperPort:
        """Given port's name, return the port as WrapperPort object.

        :raises ValueError: If such port doesn't exist.
        """
        try:
            port = getattr(self, name)
        except AttributeError:
            raise ValueError(f"Port named '{name}' couldn't be found in the hierarchy: {self.name}")
        return port

    def get_ports_of_interface(self, iface_name: str) -> List[WrapperPort]:
        """Return a list of ports of specific interface.

        :raises ValueError: if such interface doesn't exist.
        """
        ports = [port for port in filter(lambda x: x.interface_name == iface_name, self._ports)]
        if not ports:
            raise ValueError(f"No ports could be found for this interface name: {iface_name}")
        return ports
