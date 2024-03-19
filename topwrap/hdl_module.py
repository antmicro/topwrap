# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Dict, Set, Union

from .hdl_parsers_utils import PortDefinition
from .interface_grouper import InterfaceGrouper
from .ip_desc import IPCoreDescription

HDLParameter = Union[int, str, Dict[str, int]]


class HDLModule(ABC):
    def __init__(self, filename: str):
        self.filename = filename

    @property
    @abstractmethod
    def module_name(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, HDLParameter]:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def ports(self) -> Set[PortDefinition]:
        pass  # pragma: no cover

    def to_ip_core_description(self, iface_grouper: InterfaceGrouper) -> IPCoreDescription:
        mod_name = self.module_name
        parameters = self.parameters
        ports = self.ports

        iface_mappings = iface_grouper.group_to_interfaces(ports)

        return IPCoreDescription(mod_name, parameters, ports, iface_mappings)
