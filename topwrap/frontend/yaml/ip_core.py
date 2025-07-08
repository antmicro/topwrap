# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from functools import cache
from pathlib import Path
from typing import Optional, Union

from topwrap.interface import InterfaceDefinition as LegacyInterfaceDefinition
from topwrap.interface import InterfaceMode as LegacyInterfaceMode
from topwrap.interface import get_interface_by_name
from topwrap.ip_desc import (
    IPCoreComplexParameter,
    IPCoreDescription,
    IPCoreParameter,
    Signal,
)
from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    Dimensions,
    Logic,
    LogicBitSelect,
    LogicSelect,
)
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module


class IPCoreDescriptionFrontendException(Exception):
    pass


def _param_to_ir_param(par: IPCoreParameter) -> ElaboratableValue:
    if isinstance(par, IPCoreComplexParameter):
        par = f"{par.width}'d{par.value}"
    return ElaboratableValue(par)


class InterfaceDescriptionFrontend:
    @staticmethod
    @cache
    def from_loaded(name: str) -> Optional[InterfaceDefinition]:
        old = get_interface_by_name(name)
        if old is not None:
            return InterfaceDescriptionFrontend().parse(old)

    def parse(self, desc: Union[LegacyInterfaceDefinition, Path]) -> InterfaceDefinition:
        """
        Parse Interface description YAML to IR ``InterfaceDefinition``.

        :param desc: Either a deserialized interfaced description or
            a path to its YAML.
        """

        desc = LegacyInterfaceDefinition.load(desc) if isinstance(desc, Path) else desc

        intf = InterfaceDefinition(id=Identifier(name=desc.name))
        for req, sigs in ((True, desc.signals.required), (False, desc.signals.optional)):
            for dir, dirsigs in (
                (PortDirection.IN, sigs.input.items()),
                (PortDirection.OUT, sigs.output.items()),
                (PortDirection.INOUT, sigs.inout.items()),
            ):
                for name, regex in dirsigs:
                    intf.add_signal(
                        InterfaceSignal(
                            name=name,
                            type=Bit(),
                            regexp=re.compile(regex),
                            modes={
                                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                                    direction=dir, required=req
                                ),
                                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                                    direction=dir.reverse(), required=req
                                ),
                            },
                        )
                    )

        return intf


class IPCoreDescriptionFrontend:
    def parse(self, path: Path) -> Module:
        """
        Parse IP Core description YAML to IR ``Module``.

        :param desc: Path to the IP Core description YAML.
        """

        desc = IPCoreDescription.load(path)

        mod = Module(id=Identifier(name=desc.name))

        for name, param in desc.parameters.items():
            mod.add_parameter(Parameter(name=name, default_value=_param_to_ir_param(param)))

        for dir, ports in (
            (PortDirection.IN, desc.signals.input),
            (PortDirection.OUT, desc.signals.output),
            (PortDirection.INOUT, desc.signals.inout),
        ):
            for signal in ports:
                name, type, _ = self._parse_signal(signal)
                mod.add_port(Port(name=name, direction=dir, type=type))

        for iname, iface in desc.interfaces.items():
            ird = InterfaceDescriptionFrontend().from_loaded(iface.type)

            if ird is None:
                raise IPCoreDescriptionFrontendException(
                    f"Could not find interface {iface.type} among loaded interfaces"
                )

            if iface.mode is LegacyInterfaceMode.MANAGER:
                mode = InterfaceMode.MANAGER
            elif iface.mode is LegacyInterfaceMode.SUBORDINATE:
                mode = InterfaceMode.SUBORDINATE
            else:
                mode = InterfaceMode.UNSPECIFIED
            byname = {s.name: s for s in ird.signals}
            signals = {}
            for dir, sigs in (
                (PortDirection.IN, iface.signals.input),
                (PortDirection.OUT, iface.signals.output),
                (PortDirection.INOUT, iface.signals.inout),
            ):
                for sname, sig in sigs.items():
                    pname, type, slice = self._parse_signal(sig)
                    mod.add_port(port := Port(name=pname, type=type, direction=dir))
                    logic_slice = LogicSelect(logic=type)
                    if slice is not None:
                        logic_slice.ops.append(LogicBitSelect(slice))
                    signals[byname[sname]._id] = ReferencedPort.external(port, select=logic_slice)
            mod.add_interface(Interface(name=iname, mode=mode, definition=ird, signals=signals))

        return mod

    def _parse_signal(self, signal: Signal) -> tuple[str, Logic, Optional[Dimensions]]:
        data = [signal] if isinstance(signal, str) else signal
        slice = (
            Dimensions(upper=ElaboratableValue(data[3]), lower=ElaboratableValue(data[4]))
            if len(data) == 5
            else None
        )
        if len(data) == 1:
            type = Bit()
        else:
            type = Bits(
                dimensions=[
                    Dimensions(upper=ElaboratableValue(data[1]), lower=ElaboratableValue(data[2]))
                ]
            )

        return data[0], type, slice
