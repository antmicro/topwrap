# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Mapping, Set

from .hdl_parsers_utils import HDLParameter, PortDefinition
from .interface_grouper import InterfaceGrouper
from .ip_desc import (
    IPCoreComplexParameter,
    IPCoreDescription,
    IPCoreInterface,
    IPCoreIntfPorts,
    IPCorePorts,
)


class HDLModule(ABC):
    def __init__(self, path: Path):
        self.path = path

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
        ports = self.ports
        iface_mappings = iface_grouper.group_to_interfaces(ports)

        iface_ports = set()
        ifaces_by_name: Mapping[str, IPCoreInterface] = {}
        for iface in iface_mappings:
            iface_ports.update(iface.signals.values())
            ifaces_by_name[iface.name] = IPCoreInterface(
                type=iface.bus_type,
                mode=iface.mode,
                signals=IPCoreIntfPorts.from_port_def_map(
                    {iface_port.name: rtl_port for (iface_port, rtl_port) in iface.signals.items()}
                ),
            )

        p = {}
        for pname, par in self.parameters.items():
            if isinstance(par, dict):
                p[pname] = IPCoreComplexParameter(width=par["width"], value=par["value"])
            else:
                p[pname] = par

        return IPCoreDescription(
            name=self.module_name,
            signals=IPCorePorts.from_port_def_list(ports - iface_ports),
            parameters=p,
            interfaces=ifaces_by_name,
        )
