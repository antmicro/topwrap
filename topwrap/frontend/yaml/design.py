# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional, Union

from topwrap.design import DesignDescription, DesignIP, DesignSectionInterconnect
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend, _param_to_ir_param
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedIO,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Bit
from topwrap.model.interconnects.types import INTERCONNECT_TYPES
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, FileReference, Identifier
from topwrap.model.module import Module

logger = logging.getLogger(__name__)


class DesignDescriptionFrontendException(Exception):
    pass


DDFE = DesignDescriptionFrontendException


class DesignDescriptionFrontend:
    #: A list of preparsed modules by name
    _modules: dict[str, Module]

    def __init__(self, modules: Iterable[Module] = ()) -> None:
        self._modules = {m.id.name: m for m in modules}

    def parse(self, path: Path) -> Design:
        """
        Parse a design description YAML into the IR ``Design``.

        :param path: Path to the design description YAML
        """

        desc = DesignDescription.load(path)
        return self._parse_hier(path, desc, "top" if desc.design.name is None else desc.design.name)

    def _parse_hier(
        self, source: Optional[Path], desc: DesignDescription, name_hint: str
    ) -> Design:
        design = Design()
        mod = Module(
            id=Identifier(name=name_hint),
            design=design,
            refs=[FileReference(source)] if source else (),
        )

        # Parse regular component instances
        for cname, ip in desc.ips.items():
            cmod = self._get_module(ip)
            design.add_component(ModuleInstance(name=cname, module=cmod))

        # Parse hierarchical design descriptions as more components
        for hname, hdesc in desc.design.hierarchies.items():
            parsed = self._parse_hier(source, hdesc, hname)
            design.add_component(ModuleInstance(name=hname, module=parsed.parent))

        self._parse_parameters(desc, design)

        # Gather declarations of external ports and interfaces so that
        # they can be instantiated with the inferred type later on
        declared_exts = dict[str, tuple[PortDirection, bool]]()
        for port, group in ((True, desc.external.ports), (False, desc.external.interfaces)):
            for dir, decls in ((PortDirection.IN, group.input), (PortDirection.OUT, group.output)):
                for d in decls:
                    if d in declared_exts:
                        logger.warning(f"Skipping duplicated external IO: '{d}'")
                        continue
                    declared_exts[d] = (dir, port)

        # Parse regular connections between ports, interfaces and externals
        for group in (desc.design.ports, desc.design.interfaces):
            for comp, maps in group.items():
                for sig, ref in maps.items():
                    try:
                        self._parse_connection(design, declared_exts, comp, sig, ref)
                    except DDFE as e:
                        logger.warning(f"Skipping invalid connection: {e}")

        # Realize leftover, internally unconnected, external IO declarations
        for name, (dir, port) in declared_exts.items():
            if port:
                mod.add_port(Port(name=name, direction=dir, type=Bit()))
            else:
                logger.warning(
                    f"External interface '{name}' is not connected to anything in the hierarchy so"
                    f" its type cannot be resolved and it will be skipped"
                )
                continue

        # Parse interconnects
        for iname, intr in desc.design.interconnects.items():
            try:
                self._parse_interconnect(design, iname, intr)
            except DDFE as e:
                logger.warning(f"Skipping interconnect '{iname}' because of: {e}")

        # Handle the specific syntax of inout connections
        for comp, io in desc.external.ports.inout:
            try:
                refio, refsig = self._resolve_ref(design, comp, io)
                port = self._parse_external(design, refsig, io, PortDirection.INOUT, True)
                if not isinstance(refio, ReferencedPort) or not isinstance(port, Port):
                    raise DDFE("Not a port or not connected to a port")
            except DDFE as e:
                logger.warning(f"Skipping inout '{comp}.{io}' because: {e}'")
                continue

            design.add_connection(
                PortConnection(source=refio, target=ReferencedPort.external(port))
            )

        return design

    def _parse_parameters(self, desc: DesignDescription, design: Design):
        for cname, params in desc.design.parameters.items():
            comp = design.components.find_by_name(cname)
            if comp is None:
                logger.warning(f"Skipping unresolved component: '{cname}'")
                continue
            for pname, val in params.items():
                pdef = comp.module.parameters.find_by_name(pname)
                if pdef is None:
                    logger.warning(
                        f"Skipping non-existent parameter '{pname}' of component '{cname}'"
                    )
                    continue
                comp.parameters[pdef._id] = _param_to_ir_param(val)

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
        except DDFE as e:
            raise DDFE("Couldn't resolve a clock or a reset reference") from e

        if not isinstance(clock, ReferencedPort) or not isinstance(reset, ReferencedPort):
            raise DDFE("Clock or reset is not connected to a port")

        ir_intr = itype.intercon(name=iname, params=params, clock=clock, reset=reset)

        for mname, mans in intr.managers.items():
            for man in mans:
                try:
                    refio, _ = self._resolve_ref(des, mname, man)
                    if not isinstance(refio, ReferencedInterface):
                        raise DDFE("Manager reference is not an interface")
                except DDFE as e:
                    logger.warning(
                        f"Skipping manager '{man}' for interconnect '{iname}' because of: {e}"
                    )
                    continue
                ir_intr.managers[refio._id] = itype.man_params()

        for sname, subs in intr.subordinates.items():
            for sub, params in subs.items():
                try:
                    refio, _ = self._resolve_ref(des, sname, sub)
                    if not isinstance(refio, ReferencedInterface):
                        raise DDFE("Subordinate reference is not an interface")
                except DDFE as e:
                    logger.warning(
                        f"Skipping subordinate '{sub}' for interconnect '{iname}' because of: {e}"
                    )
                    continue
                ir_intr.subordinates[refio._id] = itype.sub_params.from_dict(asdict(params))

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
                raise DDFE(f"Design YAML references non-existent external: '{io}'")
        else:
            target_comp = des.components.find_by_name(comp)
            if target_comp is None:
                raise DDFE(f"Design YAML contains an unresolved component: '{comp}'")
            target_sig = target_comp.module.ios.find_by_name(io)
            if target_sig is None:
                raise DDFE(f"Design YAML references non-existent IO: '{io}' in component: '{comp}'")
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

        if isinstance(ref, int):
            if not isinstance(refio, ReferencedPort):
                raise DDFE(
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
                    raise DDFE(f"Connection to non-existent external: '{comp}.{sig} -> {ref}'")
            srcref = (
                ReferencedInterface.external(external)
                if isinstance(external, Interface)
                else ReferencedPort.external(external)
            )
        else:
            srcref, _ = self._resolve_ref(des, ref[0], ref[1])

        if isinstance(srcref, ReferencedPort) and isinstance(refio, ReferencedPort):
            des.add_connection(PortConnection(source=srcref, target=refio))
        elif isinstance(srcref, ReferencedInterface) and isinstance(refio, ReferencedInterface):
            des.add_connection(InterfaceConnection(source=srcref, target=refio))
        else:
            raise DDFE(
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
                raise DDFE(
                    f"External '{name}' was declared as an interface, but tries to represent a port"
                )
            io = Port(name=name, direction=dir, type=conn_to.type)
            des.parent.add_port(io)
        else:
            if is_port:
                raise DDFE(
                    f"External '{name}' was declared as a port, but tries to represent an interface"
                )
            if (
                conn_to.mode == InterfaceMode.MANAGER
                and dir != PortDirection.OUT
                or conn_to.mode == InterfaceMode.SUBORDINATE
                and dir != PortDirection.IN
            ):
                raise DDFE(
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
        mod = self._modules.get(ip.module.name)
        if mod is None:
            mod = IPCoreDescriptionFrontend().parse(ip.path)
            self._modules[mod.id.name] = mod

        return mod
