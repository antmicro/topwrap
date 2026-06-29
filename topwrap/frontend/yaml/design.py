# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, Optional, Union

import yaml

from topwrap.backend.yaml.common.ip_core_schema import param_to_ir_param
from topwrap.frontend.yaml.design_schema import (
    DesignDescription,
    DesignIP,
    DesignSectionInterconnect,
    MemoryMap,
    MemoryMapEntry,
)
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.interconnects.types import INTERCONNECT_TYPES, InterconnectTypeInfo
from topwrap.model.connections import (
    Clock,
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedIO,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.design import ClockDomain, Design, ModuleInstance, ResetDomain
from topwrap.model.hdl_types import Bit
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.memory_map import MemoryMap as IRMemoryMap
from topwrap.model.memory_map import MemoryMapSubordinate
from topwrap.model.misc import (
    ElaboratableValue,
    FileReference,
    Identifier,
    ObjectId,
    PluginMetadata,
)
from topwrap.model.module import Module
from topwrap.resource_field import RepoReferenceHandler

logger = logging.getLogger(__name__)


class DesignDescriptionFrontendException(Exception):
    pass


class DesignDescriptionFrontend:
    #: A list of preparsed modules by name
    _modules: dict[str, Module]

    def __init__(self, modules: Iterable[Module] = ()) -> None:
        self._modules = {m.id.name: m for m in modules}

    def parse_file(self, path: Path) -> Design:
        """
        Parse a design description YAML file into the IR ``Design``.

        :param path: Path to the design description YAML
        """

        desc = DesignDescription.load(path)
        return self._parse_hier(path, desc, "top" if desc.name is None else desc.name)

    def parse_str(self, source: str) -> Design:
        """
        Parse a string representation of a design description YAML into the IR ``Design``.

        :param source: Design description YAML source
        """

        desc = DesignDescription.from_yaml(source)
        return self._parse_hier(None, desc, "top" if desc.name is None else desc.name)

    def _parse_memory_maps(self, des: Design, memory_maps: Dict[str, MemoryMap]):
        ir_maps = dict[str, IRMemoryMap]()
        for map_name, memory_map in memory_maps.items():
            map = dict[int, ReferencedInterface]()
            for module_name, entry_or_entries in memory_map.items():
                try:
                    component = des.components.find_by_name_or_error(module_name)
                    if isinstance(entry_or_entries, MemoryMapEntry):
                        # yaml don't specify iface
                        entry: MemoryMapEntry = entry_or_entries
                        ifaces = component.module.interfaces
                        # so there should be only one iface in module
                        if len(ifaces) > 1:
                            raise DesignDescriptionFrontendException(
                                "subordinate has more that one interface, it is needed "
                                "to specify which one needs to be connected"
                            )
                        if len(ifaces) == 0:
                            raise DesignDescriptionFrontendException(
                                "subordinate doesn't have any interface"
                            )
                        ref_iface = ReferencedInterface(instance=component, io=ifaces[0])
                        map[entry.address] = MemoryMapSubordinate(ref_iface, entry.params)
                    else:
                        # yaml specified iface's
                        entries: dict[str, MemoryMapEntry] = entry_or_entries
                        for iface_name, entry in entries.items():
                            iface = component.module.interfaces.find_by_name_or_error(iface_name)
                            ref_iface = ReferencedInterface(instance=component, io=iface)
                            map[entry.address] = MemoryMapSubordinate(ref_iface, entry.params)
                except DesignDescriptionFrontendException as e:
                    logger.warning(
                        f"Skipping subordinate '{module_name}' in address map '{map_name}' "
                        f"because {e}"
                    )
            ir_maps[map_name] = IRMemoryMap(map_name, map)
        des.add_memory_maps(ir_maps)

    def _parse_components(self, desc: DesignDescription, design: Design, source: Optional[Path]):
        # Parse regular component instances
        for cname, ip in desc.ips.items():
            cmod = self._get_module(ip)
            design.add_component(ModuleInstance(name=cname, module=cmod))

        # Parse hierarchical design descriptions as more components
        for hname, hdesc in desc.hierarchies.items():
            parsed = self._parse_hier(source, hdesc, hname)
            design.add_component(ModuleInstance(name=hname, module=parsed.parent))

    def _parse_ports(self, desc: DesignDescription) -> dict[str, tuple[PortDirection, bool]]:
        declared_exts = dict[str, tuple[PortDirection, bool]]()
        for port, group in ((True, desc.external.ports), (False, desc.external.interfaces)):
            for dir, decls in ((PortDirection.IN, group.input), (PortDirection.OUT, group.output)):
                for d in decls:
                    if d in declared_exts:
                        logger.warning(f"Skipping duplicated external IO: '{d}'")
                        continue
                    declared_exts[d] = (dir, port)
        return declared_exts

    def _parse_connections(
        self,
        desc: DesignDescription,
        design: Design,
        declared_exts: dict[str, tuple[PortDirection, bool]],
    ):
        for group in (desc.connections.ports, desc.connections.interfaces):
            for comp, maps in group.items():
                for sig, ref in maps.items():
                    try:
                        self._parse_connection(design, declared_exts, comp, sig, ref)
                    except DesignDescriptionFrontendException as e:
                        logger.warning(f"Skipping invalid connection: {e}")

    def _add_ports(self, mod: Module, declared_exts: dict[str, tuple[PortDirection, bool]]):
        for name, (dir, port) in declared_exts.items():
            if port:
                mod.add_port(Port(name=name, direction=dir, type=Bit()))
            else:
                logger.warning(
                    f"External interface '{name}' is not connected to anything in the hierarchy so"
                    f" its type cannot be resolved and it will be skipped"
                )
                continue

    def _parse_interconnects(self, desc: DesignDescription, design: Design):
        for iname, intr in desc.interconnects.items():
            try:
                self._parse_interconnect(design, iname, intr)
            except DesignDescriptionFrontendException as e:
                logger.warning(f"Skipping interconnect '{iname}' because of: {e}")

    def _parse_inout(self, desc: DesignDescription, design: Design):
        for comp, io in desc.external.ports.inout:
            try:
                refio, refsig = self._resolve_ref(design, comp, io)
                port = self._parse_external(design, refsig, io, PortDirection.INOUT, True)
                if not isinstance(refio, ReferencedPort) or not isinstance(port, Port):
                    raise DesignDescriptionFrontendException(
                        "Not a port or not connected to a port"
                    )
            except DesignDescriptionFrontendException as e:
                logger.warning(f"Skipping inout '{comp}.{io}' because: {e}'")
                continue

            design.add_connection(
                PortConnection(source=refio, target=ReferencedPort.external(port))
            )

    def _parse_hier(
        self, source: Optional[Path], desc: DesignDescription, name_hint: str
    ) -> Design:
        design = Design()
        args = {"name": name_hint}
        if desc.vendor is not None:
            args["vendor"] = desc.vendor
        if desc.library is not None:
            args["library"] = desc.library
        mod = Module(
            id=Identifier(**args),
            design=design,
            refs=[FileReference(source)] if source else (),
        )

        self._parse_components(desc, design, source)
        self._parse_parameters(desc, design)

        # Gather declarations of external ports and interfaces so that
        # they can be instantiated with the inferred type later on
        declared_exts = self._parse_ports(desc)
        # Parse regular connections between ports, interfaces and externals
        self._parse_connections(desc, design, declared_exts)
        # Realize leftover, internally unconnected, external IO declarations
        self._add_ports(mod, declared_exts)

        # Parse memory maps, need to be done after interfaces are parsed
        self._parse_memory_maps(design, desc.memory_maps)

        # Parse interconnects
        self._parse_interconnects(desc, design)

        # Handle the specific syntax of inout connections
        self._parse_inout(desc, design)

        self._parse_clocks_resets(design, desc)

        self._parse_extensions(design, desc)

        return design

    def _parse_extensions(self, des: Design, desc: DesignDescription):
        for plugin_name, metadata in desc.extensions.items():
            md = PluginMetadata(name=plugin_name, data=metadata)
            des.add_metadata(md)

    def _parse_parameters(self, desc: DesignDescription, design: Design):
        for cname, ip in desc.ips.items():
            comp = design.components.find_by_name(cname)
            if comp is None:
                logger.warning(f"Skipping unresolved component: '{cname}'")
                continue
            for pname, val in ip.parameters.items():
                pdef = comp.module.parameters.find_by_name(pname)
                if pdef is None:
                    logger.warning(
                        f"Skipping non-existent parameter '{pname}' of component '{cname}'"
                    )
                    continue

                maybe_param = param_to_ir_param(val)
                assert maybe_param is not None, "Parameter value cannot be None here"

                comp.parameters[pdef._id] = maybe_param

    def _parse_interconnect_managers(
        self,
        des: Design,
        intr: DesignSectionInterconnect,
        ir_intr: Interconnect,
        itype: InterconnectTypeInfo,
        iname: str,
    ):
        def get_refio_from_manager(
            des: Design, mname: str, man: str
        ) -> Optional[ReferencedInterface]:
            try:
                refio, _ = self._resolve_ref(des, mname, man)
                if not isinstance(refio, ReferencedInterface):
                    raise DesignDescriptionFrontendException(
                        "Manager reference is not an interface"
                    )
                else:
                    return refio
            except DesignDescriptionFrontendException as e:
                logger.warning(
                    f"Skipping manager '{man}' for interconnect '{iname}' because of: {e}"
                )

        for mname, mans in intr.managers.items():
            if isinstance(mans, list):
                for man in mans:
                    refio = get_refio_from_manager(des, mname, man)
                    if not refio:
                        continue
                    ir_intr.managers[refio._id] = itype.man_params()
            else:  # Dict
                for man, params in mans.items():
                    refio = get_refio_from_manager(des, mname, man)
                    if not refio:
                        continue
                    ir_intr.managers[refio._id] = itype.man_params.from_dict(params)

    def _parse_interconnect_subordinates(
        self,
        des: Design,
        intr: DesignSectionInterconnect,
        ir_intr: Interconnect,
        itype: InterconnectTypeInfo,
        iname: str,
    ):
        for sname, subs in intr.subordinates.items():
            for sub, params in subs.items():
                try:
                    refio, _ = self._resolve_ref(des, sname, sub)
                    if not isinstance(refio, ReferencedInterface):
                        raise DesignDescriptionFrontendException(
                            "Subordinate reference is not an interface"
                        )
                except DesignDescriptionFrontendException as e:
                    logger.warning(
                        f"Skipping subordinate '{sub}' for interconnect '{iname}' because of: {e}"
                    )
                    continue
                ir_intr.subordinates[refio._id] = itype.sub_params.from_dict(asdict(params))

    def _parse_interconnect(self, des: Design, iname: str, intr: DesignSectionInterconnect):
        itype = INTERCONNECT_TYPES[intr.type]
        params = itype.params.from_dict(intr.params)
        try:
            clock, _ = self._resolve_ref(
                des, *([None, intr.clock] if isinstance(intr.clock, str) else [*intr.clock])
            )
            reset, _ = self._resolve_ref(
                des, *([None, intr.reset] if isinstance(intr.reset, str) else [*intr.reset])
            )
        except DesignDescriptionFrontendException as e:
            raise DesignDescriptionFrontendException(
                "Couldn't resolve a clock or a reset reference"
            ) from e

        if not isinstance(clock, ReferencedPort) or not isinstance(reset, ReferencedPort):
            raise DesignDescriptionFrontendException("Clock or reset is not connected to a port")

        mem_map = None
        try:
            if intr.memory_map is not None:
                if intr.memory_map not in des.memory_maps:
                    raise DesignDescriptionFrontendException(
                        f"Memory map: '{intr.memory_map}' is not defined"
                    )
                else:
                    mem_map = des.memory_maps[intr.memory_map]
        except DesignDescriptionFrontendException as e:
            logger.warning(f"Skipping memory map in '{iname}' interconnect, because of: {e}")

        ir_intr = itype.intercon(
            name=iname, params=params, clock=clock, reset=reset, memory_map=mem_map
        )

        self._parse_interconnect_managers(des, intr, ir_intr, itype, iname)
        self._parse_interconnect_subordinates(des, intr, ir_intr, itype, iname)

        des.add_interconnect(ir_intr)

    def _resolve_ref(
        self, des: Design, comp: Optional[str], io: str
    ) -> tuple[ReferencedIO, Union[Port, Interface]]:
        """
        Resolve a YAML-styled reference (described by the ``Signal`` type from
        ``ip_desc.py``) to a port of interface, to our IR's ``ReferencedIO``.

        :param des: Current design hierarchy
        :param comp: The name of the component containing the referenced IO.
            If ``None`` then the reference is to an external port
        :param io: The name of the referenced IO
        """

        if comp is None:
            target_comp = None
            target_sig = des.parent.ios.find_by_name(io)
            if target_sig is None:
                raise DesignDescriptionFrontendException(
                    f"Design YAML references non-existent external: '{io}'"
                )
        else:
            target_comp = des.components.find_by_name(comp)
            if target_comp is None:
                raise DesignDescriptionFrontendException(
                    f"Design YAML contains an unresolved component: '{comp}'"
                )
            target_sig = target_comp.module.ios.find_by_name(io)
            if target_sig is None:
                raise DesignDescriptionFrontendException(
                    f"Design YAML references non-existent IO: '{io}' in component: '{comp}'"
                )
        refio = (
            ReferencedInterface(instance=target_comp, io=target_sig)
            if isinstance(target_sig, Interface)
            else ReferencedPort(instance=target_comp, io=target_sig)
        )
        return refio, target_sig

    def _parse_connection(
        self,
        des: Design,
        decls: dict[str, tuple[PortDirection, bool]],
        comp: str,
        sig: str,
        ref: Union[int, str, tuple[str, str]],
    ):
        refio, refsig = self._resolve_ref(des, comp, sig)
        inverted = False

        # Try parse the ref if it's inverted
        if isinstance(ref, str) and ref.startswith("~"):
            inverted = True
            ref = ref[1:]
            ref = yaml.safe_load(ref)
            pass

        if isinstance(ref, int):
            if inverted:
                raise DesignDescriptionFrontendException(
                    f"Attempted to invert a constant value: '{comp}.{sig} -> ~{ref}'"
                )
            if not isinstance(refio, ReferencedPort):
                raise DesignDescriptionFrontendException(
                    f"Attempted constant connection to an interface: '{comp}.{sig} -> {ref}'"
                )
            des.add_connection(ConstantConnection(source=ElaboratableValue(ref), target=refio))
            return
        elif isinstance(ref, str):
            external = des.parent.ios.find_by_name(ref)
            if external is None:
                if ref in decls:
                    external = self._parse_external(des, refsig, ref, decls[ref][0], decls[ref][1])
                    del decls[ref]
                else:
                    raise DesignDescriptionFrontendException(
                        f"Connection to non-existent external: '{comp}.{sig} -> {ref}'"
                    )
            srcref = (
                ReferencedInterface.external(external)
                if isinstance(external, Interface)
                else ReferencedPort.external(external)
            )
        else:
            srcref, _ = self._resolve_ref(des, ref[0], ref[1])

        if isinstance(srcref, ReferencedPort) and isinstance(refio, ReferencedPort):
            des.add_connection(PortConnection(source=srcref, target=refio, invert=inverted))
        elif isinstance(srcref, ReferencedInterface) and isinstance(refio, ReferencedInterface):
            if inverted:
                raise DesignDescriptionFrontendException(
                    f"Attempted to invert an interface connection: '{comp}.{sig} -> ~{ref}'."
                )

            des.add_connection(InterfaceConnection(source=srcref, target=refio))
        else:
            raise DesignDescriptionFrontendException(
                f"IO type mismatch: '{comp}.{sig}' is {type(refio)}, but '{ref}' is {type(srcref)}"
            )

    def _parse_external(
        self,
        des: Design,
        conn_to: Union[Port, Interface],
        name: str,
        dir: PortDirection,
        is_port: bool,
    ) -> Union[Port, Interface]:
        """
        Add an external IO to the design with its type inferred
        from the other side of the connection.
        """

        if isinstance(conn_to, Port):
            if not is_port:
                raise DesignDescriptionFrontendException(
                    f"External '{name}' was declared as an interface, but tries to represent a port"
                )
            io = Port(name=name, direction=dir, type=conn_to.type)
            des.parent.add_port(io)
        else:
            if is_port:
                raise DesignDescriptionFrontendException(
                    f"External '{name}' was declared as a port, but tries to represent an interface"
                )
            if (
                conn_to.mode == InterfaceMode.MANAGER
                and dir != PortDirection.OUT
                or conn_to.mode == InterfaceMode.SUBORDINATE
                and dir != PortDirection.IN
            ):
                raise DesignDescriptionFrontendException(
                    f"External interface '{name}' was declared as {dir}, "
                    f"but is connected to {conn_to.mode}"
                )
            io = Interface(
                name=name,
                mode=conn_to.mode,
                definition=conn_to.definition,
                signals={s: None for s in conn_to.signals},
            )
            des.parent.add_interface(io)

        return io

    def _get_module(self, ip: DesignIP) -> Module:
        from topwrap.repo.user_repo import Core

        if isinstance(ip.file, RepoReferenceHandler):
            key = list(ip.file.args)[0] + ip.file.value
            mod = self._modules.get(key)
            if mod is not None:
                return mod
            mod = ip.file.to_resource(Core).top
            if mod.id.name in self._modules:
                mod = self._modules[mod.id.name]
            else:
                self._modules[mod.id.name] = mod
            self._modules[key] = mod
        else:
            mod = self._modules.get(ip.module.id.name)
            if mod is None:
                mod = IPCoreDescriptionFrontend().parse_file(ip.path)
                self._modules[mod.id.name] = mod

        return mod

    def _parse_clock_reset_domains(self, design: Design, desc: DesignDescription):
        for name, domain in desc.clock_domains.items():
            if isinstance(domain.signal, str):
                comp = None
                sig = domain.signal
            else:
                comp, sig = domain.signal

            refio, _ = self._resolve_ref(design, comp, sig)

            if isinstance(refio, ReferencedInterface):
                raise DesignDescriptionFrontendException(
                    f"Attempted to use interface '{domain.signal}' as clock signal"
                )

            design.add_clock_domain(
                ClockDomain(
                    name=name,
                    clock=refio,
                )
            )

        for name, domain in desc.reset_domains.items():
            if isinstance(domain.signal, str):
                comp = None
                sig = domain.signal
            else:
                comp, sig = domain.signal

            refio, _ = self._resolve_ref(design, comp, sig)

            if isinstance(refio, ReferencedInterface):
                raise DesignDescriptionFrontendException(
                    f"Attempted to use interface '{domain.signal}' as reset signal"
                )

            synchronous_to = (
                design.clock_domains.find_by_name(domain.synchronous_to)
                if domain.synchronous_to is not None
                else None
            )

            if synchronous_to is None and domain.synchronous_to is not None:
                raise DesignDescriptionFrontendException(
                    f"Attempted to use non-existent clock domain '{domain.synchronous_to}'"
                    f" for reset domain '{name}'"
                )

            design.add_reset_domain(
                ResetDomain(
                    name=name,
                    reset=refio,
                    polarity=ResetPolarity(domain.polarity),
                    synchronous_to=synchronous_to,
                )
            )

    def _parse_clock_reset_assignments(
        self, design: Design, name: str, mod: Module, ip: DesignIP
    ) -> tuple[dict[ObjectId[Clock], ClockDomain], dict[ObjectId[Reset], ResetDomain]]:
        clock_dom_names = {}
        for cname, dname in ip.clocks.items():
            clock = mod.clocks.find_by_name(cname)
            if clock is None:
                raise DesignDescriptionFrontendException(
                    f"Instance '{name}' of module '{mod.id.name}' references "
                    f"non-existent clock '{cname}'"
                )
            clock_dom_names[clock._id] = dname

        # Assign default domain to all unmentioned clocks
        for clock in mod.clocks:
            if clock._id in clock_dom_names:
                continue
            clock_dom_names[clock._id] = "default"

        reset_dom_names = {}
        for rname, dname in ip.resets.items():
            reset = mod.resets.find_by_name(rname)
            if reset is None:
                raise DesignDescriptionFrontendException(
                    f"Instance '{name}' of module '{mod.id.name}' references "
                    f"non-existent reset '{rname}'"
                )
            reset_dom_names[reset._id] = dname

        # Assign default domain to all unmentioned resets
        for reset in mod.resets:
            if reset._id in reset_dom_names:
                continue
            reset_dom_names[reset._id] = "default"

        clocks = {}
        for cid, dname in clock_dom_names.items():
            dom = design.clock_domains.find_by_name(dname)
            if dom is None:
                raise DesignDescriptionFrontendException(
                    f"Clock '{cid.resolve().name}' of instance '{name}' of "
                    f"module '{mod.id.name}' references non-existent clock domain '{dname}'"
                )
            clocks[cid] = dom

        resets = {}
        for rid, dname in reset_dom_names.items():
            dom = design.reset_domains.find_by_name(dname)
            if dom is None:
                raise DesignDescriptionFrontendException(
                    f"Reset '{rid.resolve().name}' of instance '{name}' of "
                    f"module '{mod.id.name}' references non-existent reset domain '{dname}'"
                )
            resets[rid] = dom

        return clocks, resets

    def _parse_clocks_resets(self, design: Design, desc: DesignDescription):
        self._parse_clock_reset_domains(design, desc)

        for cname, ip in desc.ips.items():
            cmod = self._get_module(ip)
            clocks, resets = self._parse_clock_reset_assignments(design, cname, cmod, ip)

            inst = design.components.find_by_name(cname)
            assert inst is not None

            inst.clocks.update(clocks)
            inst.resets.update(resets)

        design.lower_domains()
