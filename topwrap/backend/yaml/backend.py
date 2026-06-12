# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

from typing_extensions import override

from topwrap.backend.backend import Backend, BackendOutputInfo
from topwrap.backend.yaml.common.interface_schema import InterfaceModeDescription
from topwrap.backend.yaml.common.ip_core_schema import (
    IPCoreComplexSignal,
    IPCoreDescription,
    IPCoreInterface,
    IPCoreIntfPorts,
    IPCoreParameter,
    IPCorePorts,
    Signal,
)
from topwrap.model.connections import (
    Port,
    PortDirection,
)
from topwrap.model.hdl_types import Bit, Bits, BitStruct, Logic, LogicBitSelect
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
)
from topwrap.model.misc import ElaboratableValue, Parameter, QuerableView
from topwrap.model.module import Module


@dataclass
class IpCoreDescriptionOutput:
    base_name: str
    description: IPCoreDescription


class IpCoreDescriptionBackend(Backend[IpCoreDescriptionOutput]):
    def __init__(
        self,
        existing_interfaces: Iterable[InterfaceDefinition] = (),
    ) -> None:
        super().__init__(existing_interfaces)

    @override
    def represent(self, module: Module) -> IpCoreDescriptionOutput:
        """
        :param module: Top module to represent.
        """

        ports = self._represent_ports(module.ports)
        intfs = {intf.name: self._represent_intf(intf) for intf in module.interfaces}
        params = self._represent_params(module.parameters)

        desc = IPCoreDescription(
            id=module.id,
            signals=ports,
            parameters=params,
            interfaces=intfs,
        )

        return IpCoreDescriptionOutput(base_name=module.id.name, description=desc)

    def _represent_signal(
        self,
        name: str,
        type: Logic,
        slice: Optional[tuple[str, str]] = None,
        default: Optional[ElaboratableValue] = None,
    ) -> Signal:
        bound = None

        if isinstance(type, Bit) or isinstance(type, BitStruct):
            if slice:
                raise ValueError("Trying to slice a single bit or bit struct")
        elif isinstance(type, Bits):
            if len(type.dimensions) > 1:
                raise ValueError("IP core YAML format only supports one-dimensional bit vectors")

            bound = (type.dimensions[0].upper.value, type.dimensions[0].lower.value)
        else:
            logging.warning(f"Got unexpected type {type} for signal in IP core YAML backend")

        return IPCoreComplexSignal(
            name=name,
            bound=bound,
            slice=slice,
            default=default.value if default else None,
        )

    def _represent_ports(self, ports: QuerableView[Port]) -> IPCorePorts:
        input, output, inout = set[Signal](), set[Signal](), set[Signal]()
        for port in ports:
            represented_sig = self._represent_signal(port.name, port.type, None, port.default_value)
            if port.direction == PortDirection.IN:
                input.add(represented_sig)
            elif port.direction == PortDirection.OUT:
                output.add(represented_sig)
            else:
                assert port.direction == PortDirection.INOUT
                inout.add(represented_sig)

        return IPCorePorts(input, output, inout)

    def _represent_intf(self, intf: Interface) -> IPCoreInterface:
        mode = InterfaceModeDescription.UNSPECIFIED
        if intf.mode == InterfaceMode.MANAGER:
            mode = InterfaceModeDescription.MANAGER
        elif intf.mode == InterfaceMode.SUBORDINATE:
            mode = InterfaceModeDescription.SUBORDINATE

        input, output, inout = (
            dict[str, Optional[Signal]](),
            dict[str, Optional[Signal]](),
            dict[str, Optional[Signal]](),
        )
        for sig, port in intf.signals.items():
            dir = sig.resolve().modes[intf.mode].direction
            io = port.io if port else None
            select = port.select if port else None

            slice = None
            if select and len(select.ops) > 0:
                if not isinstance(select.ops[0], LogicBitSelect):
                    raise ValueError("IP core YAML format only supports bit slicing ports")

                if len(select.ops) > 1:
                    raise ValueError("IP core YAML format only supports single level of slice")

                if not io:
                    raise ValueError("Trying to slice an independent signal")

                slice = (select.ops[0].slice.upper.value, select.ops[0].slice.lower.value)

            represented_sig = None
            if io:
                represented_sig = self._represent_signal(io.name, io.type, slice)

            if dir == PortDirection.IN:
                input[sig.resolve().name] = represented_sig
            elif dir == PortDirection.OUT:
                output[sig.resolve().name] = represented_sig
            else:
                assert dir == PortDirection.INOUT
                inout[sig.resolve().name] = represented_sig

        return IPCoreInterface(
            type=intf.definition.id,
            mode=mode,
            signals=IPCoreIntfPorts(input, output, inout),
        )

    def _represent_params(self, params: Iterable[Parameter]) -> dict[str, IPCoreParameter]:
        out = {}

        for param in params:
            if param.default_value:
                out[param.name] = param.default_value.value
            else:
                out[param.name] = None

        return out

    @override
    def serialize(self, repr: IpCoreDescriptionOutput) -> Iterator[BackendOutputInfo]:
        out = repr.description.to_yaml()
        yield BackendOutputInfo(content=out, filename=f"{repr.base_name}.yaml")
