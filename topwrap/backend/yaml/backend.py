# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Union

import yaml
from typing_extensions import Any, override

from topwrap.backend.backend import Backend, BackendOutputInfo
from topwrap.backend.yaml.common.interface_schema import InterfaceModeDescription
from topwrap.backend.yaml.common.ip_core_schema import (
    IPCoreComplexSignal,
    IPCoreDescription,
    IPCoreInterface,
    IPCoreIntfPorts,
    IPCoreParameter,
    IPCorePorts,
    IPCoreStruct,
    IPCoreStructField,
    IPCoreType,
    Signal,
)
from topwrap.frontend.yaml.design_schema import (
    ConnectionsSection,
    DesignDescription,
    DesignExternalIntfs,
    DesignExternalPorts,
    DesignExternalSection,
    DesignIP,
    DesignSectionClockDomain,
    DesignSectionInterconnect,
    DesignSectionResetDomain,
    DS_InterfacesT,
    DS_PortsT,
    MemoryMapSubordinate,
)
from topwrap.interconnects.types import INTERCONNECT_NAMES
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedIO,
)
from topwrap.model.design import ClockDomain, Design, ModuleInstance, ResetDomain
from topwrap.model.hdl_types import Bit, Bits, BitStruct, Logic, LogicArray, LogicBitSelect
from topwrap.model.inference.port import PortSelector
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
)
from topwrap.model.memory_map import MemoryMap
from topwrap.model.misc import ElaboratableValue, ExtensionData, Parameter
from topwrap.model.module import Module
from topwrap.resource_field import FileReferenceHandler, RepoReferenceHandler
from topwrap.util import get_config

logger = logging.getLogger(__name__)


@dataclass
class IpCoreDescriptionOutput:
    base_name: str
    description: IPCoreDescription


@dataclass
class DesignDescriptionOutput:
    base_name: str
    description: DesignDescription


class DesignDescriptionBackendException(Exception):
    pass


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

        needed_ports = [
            port for port in module.ports if not self._is_trivial_type(port.type)
        ] + list(module.non_intf_ports())

        ports = self._represent_ports(needed_ports)
        intfs = {intf.name: self._represent_intf(intf) for intf in module.interfaces}
        params = self._represent_params(module.parameters)
        types = self._represent_nontrivial_types(module.ports)
        extensions = self._represent_extensions(module.extensions)

        desc = IPCoreDescription(
            id=module.id,
            signals=ports,
            parameters=params,
            interfaces=intfs,
            types=types,
            extensions=extensions,
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

        if isinstance(type, BitStruct):
            if slice:
                raise ValueError("Trying to slice a bit struct")

            type_name = type.name if type.name is not None else f"tw_anon_type_{type._id._id}"
            return IPCoreComplexSignal(
                name=name,
                type=type_name,
            )
        if isinstance(type, Bit):
            if slice:
                raise ValueError("Trying to slice a single bit")
        elif isinstance(type, Bits):
            if len(type.dimensions) > 1:
                raise ValueError("IP core YAML format only supports one-dimensional bit vectors")

            bound = (type.dimensions[0].upper.value, type.dimensions[0].lower.value)
        else:
            logger.warning(f"Got unexpected type {type} for signal in IP core YAML backend")

        return IPCoreComplexSignal(
            name=name,
            bound=bound,
            slice=slice,
            default=default.value if default else None,
        )

    def _represent_ports(self, ports: Iterable[Port]) -> IPCorePorts:
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
            use_path = False
            if select and len(select.ops) > 0:
                if not isinstance(select.ops[0], LogicBitSelect):
                    use_path = True

                if len(select.ops) > 1:
                    use_path = True

                if not io:
                    raise ValueError("Trying to slice an independent signal")

                if not use_path:
                    assert isinstance(select.ops[0], LogicBitSelect)
                    slice = (select.ops[0].slice.upper.value, select.ops[0].slice.lower.value)

            if use_path:
                assert port is not None
                represented_sig = IPCoreComplexSignal(path=PortSelector.from_referenced_port(port))
            else:
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

    def _represent_type(self, type: Logic) -> IPCoreType:
        if isinstance(type, Bit):
            return (0, 0)
        elif isinstance(type, LogicArray):
            dim = type.dimensions[0]

            if not isinstance(type.item, Bit):
                logger.warning(f"Logic array of non-bits {type.item} {type.item.name}")

            return (dim.upper.value, dim.lower.value)
        elif isinstance(type, BitStruct):
            return IPCoreStruct(
                members=[
                    IPCoreStructField(field.field_name, self._represent_type(field.type))
                    for field in type.fields
                ],
            )
        else:
            raise ValueError(f"Unexpected type {type} {type.name}")

    def _is_trivial_type(self, type: Logic) -> bool:
        if isinstance(type, Bit):
            return True
        elif isinstance(type, LogicArray):
            return True
        elif isinstance(type, BitStruct):
            return False
        else:
            raise ValueError(f"Unexpected type {type} {type.name}")

    def _represent_nontrivial_types(self, ports: Iterable[Port]) -> dict[str, IPCoreType]:
        out = {}
        for port in ports:
            if self._is_trivial_type(port.type):
                continue

            type_name = (
                port.type.name
                if port.type.name is not None
                else f"tw_anon_type_{port.type._id._id}"
            )
            out[type_name] = self._represent_type(port.type)

        return out

    def _represent_extensions(self, extensions: Iterable[ExtensionData]) -> dict[str, Any]:
        extensions_dict: dict[str, Any] = {}

        for ext_data in extensions:
            extensions_dict[ext_data.name] = ext_data.data

        return extensions_dict

    @override
    def serialize(self, repr: IpCoreDescriptionOutput) -> Iterator[BackendOutputInfo]:
        out = repr.description.to_yaml()
        yield BackendOutputInfo(content=out, filename=f"{repr.base_name}.yaml")


class DesignDescriptionBackend(Backend[DesignDescriptionOutput]):
    @override
    def represent(self, module: Module) -> DesignDescriptionOutput:
        """
        :param module: Top module to represent.
        """

        if module.design is None:
            raise DesignDescriptionBackendException(
                f"Module '{module.id.name}' with no design given to DesignDescriptionBackend"
            )

        return DesignDescriptionOutput(
            base_name=module.id.name, description=self._represent_hier(module.design)
        )

    def _represent_hier(self, design: Design) -> DesignDescription:
        ips = {}
        hierarchies = {}

        for comp in design.components:
            if comp.module.design is not None:
                hierarchies[comp.name] = self._represent_hier(comp.module.design)
            else:
                ips[comp.name] = self._represent_ip(comp)

        connections = self._represent_connections(design)
        interconnects = {
            intr.name: self._represent_interconnect(intr, design) for intr in design.interconnects
        }
        external = self._represent_externals(design.parent)
        clock_domains = {
            dom.name: self._represent_clock_domain(dom) for dom in design.clock_domains
        }
        reset_domains = {
            dom.name: self._represent_reset_domain(dom) for dom in design.reset_domains
        }
        memory_maps = {
            name: self._represent_memory_map(mmap) for name, mmap in design.memory_maps.items()
        }

        extensions = self._represent_extensions(design.extensions)

        id = design.parent.id
        return DesignDescription(
            name=id.name,
            library=id.library,
            vendor=id.vendor,
            hierarchies=hierarchies,
            ips=ips,
            connections=connections,
            interconnects=interconnects,
            external=external,
            clock_domains=clock_domains,
            reset_domains=reset_domains,
            memory_maps=memory_maps,
            extensions=extensions,
        )

    def _represent_ip(self, comp: ModuleInstance) -> DesignIP:
        source = None

        # Check repos for the module
        # Imported here due to circular import
        from topwrap.repo.user_repo import Core

        for name, repo in get_config().loaded_repos.items():
            for core in repo.get_resources(Core):
                if core.top is comp.module:
                    source = RepoReferenceHandler(core.name, [name])
                    break

        # Fall back to file path
        if source is None:
            if not comp.module.refs:
                raise DesignDescriptionBackendException(
                    f"Cannot determine source for module {comp.module.id.name}: "
                    "It does not belong to any repository, and has no file references."
                )

            source = FileReferenceHandler(comp.module.refs[0].file)

        return DesignIP(
            file=source,
            parameters={p.resolve().name: v.value for p, v in comp.parameters.items()},
            clocks={c.resolve().name: d.name for c, d in comp.clocks.items()},
            resets={r.resolve().name: d.name for r, d in comp.resets.items()},
        )

    def _represent_connections(self, des: Design) -> ConnectionsSection:
        return ConnectionsSection(
            ports=self._represent_port_conns(des),
            interfaces=self._represent_intf_conns(des),
        )

    def _represent_port_conns(self, des: Design) -> DS_PortsT:
        out = {}

        for conn in des.connections:
            if isinstance(conn, PortConnection):
                lhs, rhs = conn.target, conn.source
                if lhs.instance is None:
                    lhs, rhs = rhs, lhs

                if lhs.instance is None:
                    raise DesignDescriptionBackendException(
                        f"Connection between external ports '{lhs.io.name}' and "
                        f"'{rhs.io.name}' is not representable in design YAML"
                    )

                if lhs.instance.name not in out:
                    out[lhs.instance.name] = {}

                if not conn.invert:
                    out[lhs.instance.name][lhs.io.name] = self._represent_ref_io(rhs)
                else:
                    io = self._represent_ref_io(rhs)
                    if isinstance(io, str):
                        rep = io
                    else:
                        rep = yaml.safe_dump(io, default_flow_style=True).strip()
                    out[lhs.instance.name][lhs.io.name] = f"~{rep}"
            elif isinstance(conn, ConstantConnection):
                lhs = conn.target
                if lhs.instance is None:
                    raise DesignDescriptionBackendException(
                        f"Constant connection to external port '{lhs.io.name}' "
                        "is not representable in design YAML"
                    )

                if lhs.instance.name not in out:
                    out[lhs.instance.name] = {}

                out[lhs.instance.name][lhs.io.name] = conn.source.value

        return out

    def _represent_intf_conns(self, des: Design) -> DS_InterfacesT:
        out = {}

        for conn in des.connections:
            if isinstance(conn, InterfaceConnection):
                lhs, rhs = conn.target, conn.source
                if lhs.instance is None:
                    lhs, rhs = rhs, lhs

                if lhs.instance is None:
                    raise DesignDescriptionBackendException(
                        f"Connection between external interfaces '{lhs.io.name}' "
                        f"and '{rhs.io.name}' is not representable in design YAML"
                    )

                if lhs.instance.name not in out:
                    out[lhs.instance.name] = {}

                out[lhs.instance.name][lhs.io.name] = self._represent_ref_io(rhs)

        return out

    def _represent_interconnect(self, intr: Interconnect, des: Design) -> DesignSectionInterconnect:
        managers = {}

        for i_mgr, par in intr.managers.items():
            i_mgr = i_mgr.resolve()

            # if mgr is external, set its name to toplevel's name
            instance_name = des.parent.id.name if i_mgr.instance is None else i_mgr.instance.name

            if instance_name not in managers:
                managers[instance_name] = {}

            managers[instance_name][i_mgr.io.name] = par.to_dict()

        subordinates = {}

        for i_sub, par in intr.subordinates.items():
            i_sub = i_sub.resolve()

            # if sub is external, set its name to toplevel's name
            instance_name = des.parent.id.name if i_sub.instance is None else i_sub.instance.name

            # Skip subordinates covered by a memory map
            if intr.memory_map:
                for m_sub in intr.memory_map.map.values():
                    if i_sub == m_sub.ref_iface:
                        continue

            if instance_name not in subordinates:
                subordinates[instance_name] = {}

            subordinates[instance_name][i_sub.io.name] = par.to_dict()

        return DesignSectionInterconnect(
            type=INTERCONNECT_NAMES[type(intr)],
            clock=self._represent_ref_io(intr.clock),
            reset=self._represent_ref_io(intr.reset),
            params=intr.params.to_dict(),
            managers=managers,
            subordinates=subordinates,
            memory_map=intr.memory_map and intr.memory_map.name,
        )

    def _represent_externals(self, mod: Module) -> DesignExternalSection:
        return DesignExternalSection(
            ports=self._represent_external_ports(mod),
            interfaces=self._represent_external_intfs(mod),
        )

    def _represent_external_ports(self, mod: Module) -> DesignExternalPorts:
        inputs = []
        outputs = []
        inouts = []

        for port in mod.non_intf_ports():
            if port.direction is PortDirection.IN:
                inputs.append(port.name)
            elif port.direction is PortDirection.OUT:
                outputs.append(port.name)
            elif port.direction is PortDirection.INOUT:
                # Look for connection that this port is a part of, then from that
                # find the module port it's connected to.
                des = mod.design
                assert des is not None
                found = False

                for conn in des.connections:
                    if isinstance(conn, PortConnection):
                        other = None
                        if conn.source.io is port:
                            other = conn.target
                        elif conn.target.io is port:
                            other = conn.source
                        if other is not None:
                            if found:
                                raise DesignDescriptionBackendException(
                                    f"Inout port {port.name} is connected to multiple modules"
                                )

                            if other.instance is None:
                                raise DesignDescriptionBackendException(
                                    f"Inout port {port.name} is connected to another external port"
                                )

                            inouts.append((other.instance.name, other.io.name))
                            found = True

                if not found:
                    raise DesignDescriptionBackendException(
                        f"Inout port {port.name} is not connected to any module port"
                    )

        return DesignExternalPorts(input=inputs, output=outputs, inout=inouts)

    def _represent_external_intfs(self, mod: Module) -> DesignExternalIntfs:
        inputs = []
        outputs = []

        for intf in mod.interfaces:
            if intf.mode is InterfaceMode.SUBORDINATE:
                inputs.append(intf.name)
            elif intf.mode is InterfaceMode.MANAGER:
                outputs.append(intf.name)
            else:
                assert intf.mode is InterfaceMode.UNSPECIFIED
                raise DesignDescriptionBackendException(
                    f"Interface '{intf.name}' with mode UNSPECIFIED is not representable "
                    "in design YAML"
                )

        return DesignExternalIntfs(input=inputs, output=outputs)

    def _represent_clock_domain(self, clock_dom: ClockDomain) -> DesignSectionClockDomain:
        return DesignSectionClockDomain(
            signal=self._represent_ref_io(clock_dom.clock),
        )

    def _represent_reset_domain(self, reset_dom: ResetDomain) -> DesignSectionResetDomain:
        return DesignSectionResetDomain(
            signal=self._represent_ref_io(reset_dom.reset),
            polarity=reset_dom.polarity.value,
            synchronous_to=reset_dom.synchronous_to and reset_dom.synchronous_to.name,
        )

    def _represent_memory_map(self, mmap: MemoryMap) -> dict[str, MemoryMapSubordinate]:
        out = {}

        for addr, sub in mmap.map.items():
            ref = sub.ref_iface

            if ref.instance is None:
                raise DesignDescriptionBackendException(
                    f"Subordinate {ref.io.name} of memory map {mmap.name} does not "
                    "connect to a module"
                )

            if ref.instance.name not in out:
                out[ref.instance.name] = {}

            params = dict[str, Union[str, int]]()
            params["address"] = addr
            params.update({name: value.value for name, value in sub.parameters.items()})
            out[ref.instance.name][ref.io.name] = params

        return out

    def _represent_extensions(self, extensions: Iterable[ExtensionData]) -> dict[str, Any]:
        extensions_dict: dict[str, Any] = {}

        for ext_data in extensions:
            extensions_dict[ext_data.name] = ext_data.data

        return extensions_dict

    def _represent_ref_io(self, ref: ReferencedIO) -> Union[str, tuple[str, str]]:
        if ref.is_external:
            return ref.io.name
        assert ref.instance is not None
        return (ref.instance.name, ref.io.name)

    @override
    def serialize(self, repr: DesignDescriptionOutput) -> Iterator[BackendOutputInfo]:
        out = repr.description.to_yaml()
        yield BackendOutputInfo(content=out, filename=f"{repr.base_name}.yaml")
