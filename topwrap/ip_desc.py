# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from collections import defaultdict
from os import path
from typing import Dict, Iterable, List, Optional, Set

import yaml
from strictyaml import (
    CommaSeparated,
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
from strictyaml.dumper import StrictYAMLDumper
from strictyaml.ruamel import dump

from .hdl_parsers_utils import PortDefinition, PortDirection
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

        # TODO: update docs on new formats
        # TODO: update examples with new formats
        # TODO: update anything that might depend on the format
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
                            "mode": Enum(["master", "slave"]),
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
            ifaces_by_dir[iface.prefix]["type"] = iface.bus_type
            # TODO: deduce mode or get rid of it entirely as there could be more configurations that don't imply master/slave
            ifaces_by_dir[iface.prefix]["mode"] = "master"
            for iface_port_name, rtl_port in iface.signals.items():
                ifaces_by_dir[iface.prefix]["signals"][rtl_port.direction.value][iface_port_name] = [
                    rtl_port.name,
                    rtl_port.upper_bound,
                    rtl_port.lower_bound,
                ]

        return ifaces_by_dir

    def save(self, filename=None):
        if filename is None:
            filename = self.name + ".yaml"

        with open(filename, "w") as f:
            ifaces_by_dir = self._group_iface_ports_by_dir(self.iface_matches)

            # ports that belong to some interface
            iface_ports = set()
            for iface in self.iface_matches:
                iface_ports.update(iface.signals.values())
            # only consider ports that aren't part of any interface
            ports_by_dir = self._group_ports_by_dir(self.ports - iface_ports)
            yaml_content = {
                "name": self.name,
                "parameters": self.parameters,
                "signals": ports_by_dir,
                "interfaces": ifaces_by_dir,
            }
            f.write(as_document(yaml_content, self.schema).as_yaml())
