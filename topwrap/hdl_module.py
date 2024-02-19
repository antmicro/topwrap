# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod

from .interface_grouper import InterfaceGrouper
from .ip_desc import IPCoreDescription


class HDLModule(ABC):
    def __init__(self, filename: str):
        self.filename = filename

    @abstractmethod
    def get_module_name(self):
        pass

    @abstractmethod
    def get_parameters(self):
        pass

    @abstractmethod
    def get_ports(self):
        pass

    def to_ip_core_description(self, iface_grouper: InterfaceGrouper) -> IPCoreDescription:
        mod_name = self.get_module_name()
        parameters = self.get_parameters()
        ports = self.get_ports()

        iface_mappings = iface_grouper.get_interface_mappings(self.filename, ports)

        return IPCoreDescription(mod_name, parameters, ports, iface_mappings)
