# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from collections import defaultdict
from typing import Dict, Iterable, List, Set

from strictyaml import (
    EmptyDict,
    EmptyList,
    Enum,
    FixedSeq,
    Int,
    Map,
    MapPattern,
    Seq,
    Str,
    as_document,
)

from .hdl_parsers_utils import PortDefinition, PortDirection
from .interface import InterfaceMode
from .interface_grouper import InterfaceMatch


class IPCoreDescription:
    def __init__(
        self,
        name: str,
        parameters: Dict[str, str],
        ports: Set[PortDefinition],
        iface_matches: Iterable[InterfaceMatch],
    ):
        self.name = name
        self.parameters = parameters
        self.ports = ports
        self.iface_matches = iface_matches

        port_schema = FixedSeq([Str(), Str(), Str()])  # alternatively CommaSeparated(Str())
        port_list_schema = Seq(port_schema) | EmptyList()
        iface_port_list_schema = MapPattern(Str(), port_schema) | EmptyDict()
        self.schema = Map(
            {
                "name": Str(),
                "parameters": MapPattern(
                    Str(), Int() | Str() | Map({"value": Int() | Str(), "width": Int()})
                )
                | EmptyDict(),
                "signals": Map(
                    {
                        PortDirection.IN.value: port_list_schema,
                        PortDirection.OUT.value: port_list_schema,
                        PortDirection.INOUT.value: port_list_schema,
                    }
                )
                | EmptyDict(),
                "interfaces": MapPattern(
                    Str(),
                    Map(
                        {
                            "signals": Map(
                                {
                                    PortDirection.IN.value: iface_port_list_schema,
                                    PortDirection.OUT.value: iface_port_list_schema,
                                    PortDirection.INOUT.value: iface_port_list_schema,
                                }
                            ),
                            "type": Str(),  # preferably enum of available interfaces
                            "mode": Enum(list(map(lambda mode: mode.value, InterfaceMode))),
                        }
                    ),
                )
                | EmptyDict(),
            }
        )

    def _group_ports_by_dir(self, ports: Iterable[PortDefinition]) -> Dict[str, List[List[str]]]:
        """Group ports by direction and transform them
        into 3-element lists of [name, upper_bound, lower_bound]

        :param ports: iterable of PortDefinition objects
        :return: dictionary in the format expected by YAML dumper:
        {
            'in': [[port1_name, port1_upper_bound, port1_lower_bound], ...]
            'out': <as above>
            'inout': <as above>
        }
        """
        ports_by_dir = {
            PortDirection.IN.value: [],
            PortDirection.OUT.value: [],
            PortDirection.INOUT.value: [],
        }

        for rtl_port in ports:
            ports_by_dir[rtl_port.direction.value].append(
                [rtl_port.name, rtl_port.upper_bound, rtl_port.lower_bound]
            )

        return ports_by_dir

    def _group_iface_ports_by_dir(
        self, iface_matches: Iterable[InterfaceMatch]
    ) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """Group ports in `iface_mappings` by direction and transform them
        into 3-element lists of [name, upper_bound, lower_bound]

        :param iface_mappings: iterable where every element has the form of:
        InterfaceMatch(
            prefix = iface_prefix,
            bus_type = iface_bus_type,
            signals = {
                iface_port1_name: PortDefinition(
                    name = rtl_port1_name
                    direction = PortDirection.<direction>
                    upper_bound = rtl_port1_upper_bound
                    lower_bound = rtl_port1_lower_bound
                ),
                ...
            }
        )

        :return: a dictionary in the format expected by YAML dumper:
        {
            iface_prefix: {
                'signals': {
                    'in': {
                        iface1_port1_name: [rtl_port1_name, rtl_port1_upper_bound, rtl_port1_lower_bound],
                        ...
                    },
                    'out': <as above>,
                    'inout': <as above>,
                },
                'type': iface_bus_type,
                'mode': 'master'|'slave'
            },
            ...
        }
        """
        ifaces_by_dir = defaultdict(
            lambda: {
                "signals": {
                    PortDirection.IN.value: {},
                    PortDirection.OUT.value: {},
                    PortDirection.INOUT.value: {},
                }
            }
        )

        for iface in iface_matches:
            ifaces_by_dir[iface.name]["type"] = iface.bus_type
            ifaces_by_dir[iface.name]["mode"] = iface.mode.value
            for iface_port, rtl_port in iface.signals.items():
                ifaces_by_dir[iface.name]["signals"][rtl_port.direction.value][iface_port.name] = [
                    rtl_port.name,
                    rtl_port.upper_bound,
                    rtl_port.lower_bound,
                ]

        return ifaces_by_dir

    def format(self):
        ifaces_by_dir = self._group_iface_ports_by_dir(self.iface_matches)

        # ports that belong to some interface
        iface_ports = set()
        for iface in self.iface_matches:
            iface_ports.update(iface.signals.values())
        # only consider ports that aren't part of any interface
        ports_by_dir = self._group_ports_by_dir(self.ports - iface_ports)
        return {
            "name": self.name,
            "parameters": self.parameters,
            "signals": ports_by_dir,
            "interfaces": ifaces_by_dir,
        }

    def save(self, filename=None):
        if filename is None:
            filename = self.name + ".yaml"

        with open(filename, "w") as f:
            f.write(as_document(self.format(), self.schema).as_yaml())
