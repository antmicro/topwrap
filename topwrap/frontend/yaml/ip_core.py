# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from typing import (
    Optional,
    Sequence,
    Union,
)

from topwrap.backend.yaml.common.interface_schema import InterfaceModeDescription
from topwrap.backend.yaml.common.ip_core_schema import (
    IPCoreComplexSignal,
    IPCoreDescription,
    IPCoreDescriptionFrontendException,
    Signal,
    param_to_ir_param,
)
from topwrap.model.connections import (
    Clock,
    Port,
    PortDirection,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    Dimensions,
    LogicBitSelect,
    LogicSelect,
)
from topwrap.model.interface import (
    Interface,
    InterfaceMode,
    InterfaceSignal,
)
from topwrap.model.misc import ElaboratableValue, FileReference, Parameter
from topwrap.model.module import Module
from topwrap.util import get_config

IPDFE = IPCoreDescriptionFrontendException


class IPCoreDescriptionFrontend:
    def parse_file(self, path: Path) -> Module:
        """
        Parse IP Core description YAML file to IR ``Module``.

        :param desc: Path to the IP Core description YAML.
        """

        desc = IPCoreDescription.load(path)
        return self._parse(path, desc)

    def parse_str(self, source: str) -> Module:
        """
        Parse a string representation of an IP Core description YAML to IR ``Module``.

        :param source: IP Core description YAML source.
        """

        desc = IPCoreDescription.from_yaml(source)
        return self._parse(None, desc)

    def _parse(self, source: Optional[Path], desc: IPCoreDescription) -> Module:
        mod = Module(id=desc.id, refs=[FileReference(source)] if source else ())

        for name, param in desc.parameters.items():
            mod.add_parameter(Parameter(name=name, default_value=param_to_ir_param(param)))

        for dir, ports in (
            (PortDirection.IN, desc.signals.input),
            (PortDirection.OUT, desc.signals.output),
            (PortDirection.INOUT, desc.signals.inout),
        ):
            for signal in ports:
                port = self._parse_signal(mod, dir, signal)

                if isinstance(port, ReferencedPort):
                    raise IPCoreDescriptionFrontendException(
                        f"Unexpected slice in definition of port '{port.io.name}'"
                    )

        self._parse_clocks_resets(desc, mod)

        self._parse_intfs(desc, mod)

        return mod

    def _parse_signal(
        self,
        mod: Module,
        direction: PortDirection,
        signal: Signal,
        intf_sig: Optional[InterfaceSignal] = None,
        intf_mode: Optional[InterfaceMode] = None,
    ) -> Union[Port, ReferencedPort]:
        def to_dims(lst: Sequence[Union[str, int]]):
            return Dimensions(
                upper=ElaboratableValue(lst[0]),
                lower=ElaboratableValue(lst[1]),
            )

        if isinstance(signal, IPCoreComplexSignal):
            if signal.name is not None:
                slice = None if signal.slice is None else to_dims(signal.slice)
                if signal.bound is None:
                    type = Bit()
                else:
                    type = Bits(dimensions=[to_dims(signal.bound)])
                default = ElaboratableValue(signal.default) if signal.default is not None else None

                if default is not None and direction is not PortDirection.IN:
                    raise IPCoreDescriptionFrontendException(
                        f"Default value '{default}' assigned to non-input port '{signal.name}'"
                    )

                if not (port := mod.ports.find_by_name(signal.name)):
                    mod.add_port(
                        port := Port(
                            name=signal.name, type=type, direction=direction, default_value=default
                        )
                    )

                if slice is not None:
                    return ReferencedPort.external(
                        port, select=LogicSelect(logic=type, ops=[LogicBitSelect(slice)])
                    )
                else:
                    return port
            else:
                assert signal.path is not None

                if intf_sig is None or intf_mode is None:
                    raise IPCoreDescriptionFrontendException(
                        f"Signal 'path': '{signal.path}' specified for non-interface signal"
                    )

                return signal.path.make_referenced_port(mod, intf_mode, intf_sig)

        data = [signal] if isinstance(signal, str) else signal
        slice = to_dims(data[3:5]) if len(data) == 5 else None
        if len(data) == 1:
            type = Bit()
        else:
            type = Bits(dimensions=[to_dims(data[1:3])])

        if not (port := mod.ports.find_by_name(data[0])):
            mod.add_port(port := Port(name=data[0], type=type, direction=direction))

        if slice is not None:
            return ReferencedPort.external(
                port, select=LogicSelect(logic=type, ops=[LogicBitSelect(slice)])
            )
        else:
            return port

    def _parse_intfs(self, desc: IPCoreDescription, mod: Module):
        # TODO: Is this best way to get existing_interfaces?
        # `_parse` method can have different effects when loaded_repos changes
        existing_interfaces = []
        from topwrap.repo.user_repo import InterfaceDefinitionResource

        for repo in get_config().loaded_repos.values():
            for res in repo.get_resources(InterfaceDefinitionResource):
                existing_interfaces.append(res.definition)

        for iname, iface in desc.interfaces.items():
            for existing_iface in existing_interfaces:
                if (
                    iface.type.name == existing_iface.id.name
                    and iface.type.library == existing_iface.id.library
                    and iface.type.vendor == existing_iface.id.vendor
                ):
                    ird = existing_iface
                    break
            else:
                raise IPCoreDescriptionFrontendException(
                    f"Could not find interface {iface.type} among loaded interfaces"
                )

            if iface.mode is InterfaceModeDescription.MANAGER:
                mode = InterfaceMode.MANAGER
            elif iface.mode is InterfaceModeDescription.SUBORDINATE:
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
                    if sig:
                        port = self._parse_signal(mod, dir, sig, byname[sname], mode)

                        if isinstance(port, Port):
                            port = ReferencedPort.external(port)

                        signals[byname[sname]._id] = port
                    else:
                        signals[byname[sname]._id] = None

            clock = mod.clocks.find_by_name(iface.clock) if iface.clock is not None else None

            if clock is None and iface.clock is not None:
                raise IPDFE(
                    f"Attempted to use non-existent clock '{iface.clock}' for interface '{iname}'"
                )

            reset = mod.resets.find_by_name(iface.reset) if iface.reset is not None else None

            if reset is None and iface.reset is not None:
                raise IPDFE(
                    f"Attempted to use non-existent reset '{iface.reset}' for interface '{iname}'"
                )

            mod.add_interface(
                Interface(
                    name=iname,
                    mode=mode,
                    definition=ird,
                    signals=signals,
                    clock=clock,
                    reset=reset,
                    size=iface.size,
                )
            )

    def _parse_clocks_resets(self, desc: IPCoreDescription, mod: Module):
        for name, domain in desc.clocks.items():
            sig = mod.ports.find_by_name(domain.signal)

            if not sig:
                raise IPDFE(f"Attempted to use non-existent port '{domain.signal}' as clock signal")

            mod.add_clock(
                Clock(
                    name=name,
                    clock=sig,
                )
            )

        for name, domain in desc.resets.items():
            sig = mod.ports.find_by_name(domain.signal)

            if not sig:
                raise IPDFE(f"Attempted to use non-existent port '{domain.signal}' as reset signal")

            synchronous_to = (
                mod.clocks.find_by_name(domain.synchronous_to)
                if domain.synchronous_to is not None
                else None
            )

            if synchronous_to is None and domain.synchronous_to is not None:
                raise IPDFE(
                    f"Attempted to use non-existent clock '{domain.synchronous_to}'"
                    f" for reset '{name}'"
                )

            mod.add_reset(
                Reset(
                    name=name,
                    reset=sig,
                    polarity=ResetPolarity(domain.polarity),
                    synchronous_to=synchronous_to,
                )
            )
