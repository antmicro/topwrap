# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar, Optional, Union

from jinja2 import Template

from topwrap.backend.sv.common import get_template, serialize_select, sv_varname
from topwrap.model.connections import (
    Connection,
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Logic, LogicSelect, has_symbolic_dimensions
from topwrap.model.interface import Interface, InterfaceDefinition
from topwrap.model.misc import ElaboratableValue, ObjectId
from topwrap.util import MISSING, unwrap_simple_parenthesized_sv_literal

logger = logging.getLogger(__name__)


@dataclass
class _SystemVerilogPartialConn:
    select: LogicSelect
    source: Union[ReferencedPort, ElaboratableValue, str]
    invert: bool


class _SystemVerilogDesignData:
    #: Contains external interfaces with independent signals
    intf_exts: dict[str, InterfaceDefinition]

    #: Interfaces that should be instantiated in the design
    #: in order to realize an `InterfaceConnection` between
    #: two components. Key is the generated name for the instance
    intf_decls: dict[str, InterfaceDefinition]

    #: Nets that should be instantiated in the design to realize
    #: sliced connections between components. Keys are nets'
    #: names and values are their types.
    nets: dict[str, Logic]

    #: A dict keyed by components instantiated in the design
    #: with values being mappings of serialized port names
    #: to expressions that the ports are connected to. Sometimes
    #: they'll be connected to nets, sometimes directly to other
    #: components, sliced or not, sometimes to interface modports and so on
    port_maps: dict[ObjectId[ModuleInstance], dict[str, str]]

    #: A map holding all ``assign`` statements that should be realized
    #: in the serialized design to connect net slices and interface
    #: signals to each other. Keys are left-hand sides of an assign
    #: statement and values are right-hand sides
    assign_map: dict[str, str]

    #: All ``design.connections`` are parsed into this temporal
    #: structure (see ``self.store_sel(...)``) which is later
    #: parsed by ``self.parse_partial_conns(...)`` to generate the
    #: port maps, assign maps and net declarations.
    #:
    #: Its keys are ports on components (or externals, ModuleInstance = None)
    #: and the values are pairs of slice of the port and the
    #: expression it's connected to. If there's only one such slice
    #: then a net is not needed and the singular expression can be
    #: directly added to the port map. When there are multiple slices,
    #: then a net is generated, a connection to that net is added to the
    #: port map and slices of that net are added to the assign map with their drivers
    conns_to_partials: dict[
        tuple[Optional[ObjectId[ModuleInstance]], ObjectId[Port]],
        list[_SystemVerilogPartialConn],
    ]

    def __init__(self) -> None:
        self.intf_exts = {}
        self.intf_decls = {}
        self.nets = {}
        self.port_maps = defaultdict(dict)
        self.assign_map = {}
        self.conns_to_partials = defaultdict(list)

    def store_sel(
        self,
        ref: ReferencedPort,
        other: Union[ReferencedPort, ElaboratableValue, str],
        invert: bool,
    ):
        """Shortcut for storing a connection to a slice of an input"""

        i = ref.instance
        self.conns_to_partials[(i if i is None else i._id, ref.io._id)].append(
            _SystemVerilogPartialConn(ref.select, other, invert)
        )

    def parse_connection(self, conn: Connection):
        if isinstance(conn, ConstantConnection):
            self.store_sel(conn.target, conn.source, False)
        elif isinstance(conn, PortConnection):
            self.handle_port_con(conn)
        elif isinstance(conn, InterfaceConnection):
            self.handle_intf_con(conn)

    def handle_port_con(self, conn: PortConnection):
        if (
            conn.source.is_external
            and conn.source.io.direction is PortDirection.OUT
            or not conn.source.is_external
            and conn.source.io.direction is PortDirection.IN
        ):
            self.store_sel(conn.source, conn.target, conn.invert)
        else:
            self.store_sel(conn.target, conn.source, conn.invert)

    def _check_warn_incompatible_intf_defs(self, conn: InterfaceConnection):
        sio = conn.source.io
        tio = conn.target.io
        sdef = sio.definition
        tdef = tio.definition
        sinst = f" in {conn.source.instance.name}" if conn.source.instance else ""
        tinst = f" in {conn.target.instance.name}" if conn.target.instance else ""

        if sdef == tdef:
            return

        logger.warning(
            f"Attempting to connect incompatible interfaces. Source port {sio.name}{sinst} uses "
            f"definition {sdef.id.name}, while target port {tio.name}{tinst} uses {tdef.id.name}."
        )

    def handle_intf_con(self, conn: InterfaceConnection):
        self._check_warn_incompatible_intf_defs(conn)

        src_ind = conn.source.io.has_independent_signals
        trg_ind = conn.target.io.has_independent_signals
        intf = None
        if src_ind or trg_ind:
            # Find what will be the interface instance, either an external
            # independent interface or a freshly created instance if no
            # external independent interfaces are involved
            if conn.source.instance is None and src_ind:
                intf = sv_varname(conn.source.io.name)
            elif conn.target.instance is None and trg_ind:
                intf = sv_varname(conn.target.io.name)
            else:
                csn = conn.source.instance.name if conn.source.instance is not None else "EXT"
                ctn = conn.target.instance.name if conn.target.instance is not None else "EXT"
                intf = sv_varname(f"{csn}__{conn.source.io.name}__{ctn}__{conn.target.io.name}")
                self.intf_decls[intf] = conn.source.io.definition

            # All internal independent interfaces must be connected to an interface instance
            if src_ind and conn.source.instance is not None:
                self.port_maps[conn.source.instance._id][conn.source.io.name] = intf
            if trg_ind and conn.target.instance is not None:
                self.port_maps[conn.target.instance._id][conn.target.io.name] = intf

        # ALL INTERFACE INSTANCES ARE CONNECTED BY THIS POINT
        # now only dependent/sliced signals are left or defaults
        for sig in conn.source.io.definition.signals:
            ssig = conn.source.io.signals.get(sig._id, MISSING)
            tsig = conn.target.io.signals.get(sig._id, MISSING)

            try:
                for side in (conn.source, conn.target):
                    if sig.modes.get(side.io.mode) is None:
                        logger.warning(
                            f"Signal '{sig.name}' of interface '{side.io.name}' "
                            f"is not allowed for '{side.io.mode}'"
                        )
                        raise ValueError()
            except ValueError:
                continue

            # Assigns default value if one signal is an input and its corresponding
            # other side is missing and the default value was defined
            for this, side, other in [(ssig, conn.source, tsig), (tsig, conn.target, ssig)]:
                if sig.modes[side.io.mode].direction is PortDirection.IN and other is MISSING:
                    # TODO: This default value assignment works only for sliced signals
                    # and will not work to assign a default value to an independent port.
                    # I believe this should be resolved together with adding support for
                    # PortConnections to interface signals.
                    if sig.default is not None and isinstance(this, ReferencedPort):
                        self.store_sel(
                            ReferencedPort(instance=side.instance, select=this.select, io=this.io),
                            sig.default,
                            False,
                        )
                        continue

            ref_port, ref_side, other_port, other_side = (
                (ssig, conn.source, tsig, conn.target)
                if isinstance(ssig, ReferencedPort)
                else (tsig, conn.target, ssig, conn.source)
            )

            # Special case, despite there being two independent signals,
            # they exist on external interfaces, which can't be connected
            # together using an SV connection between instances
            if ref_side.is_external and other_side.is_external and ref_port is other_port is None:
                left = f"{sv_varname(ref_side.io.name)}.{sv_varname(sig.name)}"
                right = f"{sv_varname(other_side.io.name)}.{sv_varname(sig.name)}"
                if sig.modes[ref_side.io.mode].direction is PortDirection.IN:
                    left, right = right, left
                self.assign_map[left] = right
            # If this is not a `ReferencedPort` then this is a connection
            # between two independent signals which was already realized
            # above while initializing interface instances and nothing else has to be done
            elif isinstance(ref_port, ReferencedPort):
                if isinstance(other_port, ReferencedPort):
                    self.handle_port_con(
                        PortConnection(
                            source=ReferencedPort(
                                instance=ref_side.instance, io=ref_port.io, select=ref_port.select
                            ),
                            target=ReferencedPort(
                                instance=other_side.instance,
                                io=other_port.io,
                                select=other_port.select,
                            ),
                        )
                    )
                    continue
                elif other_port is None:
                    assert intf is not None, (
                        "`other` being None implies `trg_ind` == True or `src_ind` == True"
                        ", which implies `intf` not being None"
                    )
                    inst = None if ref_side.instance is None else ref_side.instance._id
                    sigref = f"{intf}.{sv_varname(sig.name)}"
                    self.conns_to_partials[(inst, ref_port.io._id)].append(
                        _SystemVerilogPartialConn(ref_port.select, sigref, False)
                    )

    def _is_port_map_eligible(
        self,
        lhs: Port,
        partial: _SystemVerilogPartialConn,
    ) -> bool:
        if len(partial.select.ops) > 0:
            return False
        if not partial.invert:
            return True

        assert isinstance(partial.source, ReferencedPort)

        if lhs.direction is PortDirection.IN and partial.source.io.direction is PortDirection.OUT:
            return True

        if lhs.direction is PortDirection.IN and partial.source.is_external:
            return True

        return False

    def parse_partial_conns(self):
        """
        Goes through ``self.conns_to_partials`` in order to update the
        port map, potentially add nets and add entries to the assign map
        """
        for (instance, port), selects in self.conns_to_partials.items():
            self._parse_partial_conn_entry(instance, port.resolve(), selects)

    @staticmethod
    def _type_has_symbolic_dims(net_type: Optional[Logic]) -> bool:
        return has_symbolic_dimensions(net_type)

    @staticmethod
    def _normalize_port_expr(expr: str) -> str:
        """
        Canonicalize simple parenthesized literals to avoid emitting
        redundant wrappers in port maps, e.g. `.in((0))`.
        """
        return unwrap_simple_parenthesized_sv_literal(expr)

    def _serialize_conn_value(self, right: Union[ElaboratableValue, ReferencedPort, str]) -> str:
        if not isinstance(right, ReferencedPort):
            return str(right)
        if right.instance is None:
            return sv_varname(right.io.name) + serialize_select(right.select)
        return f"{sv_varname(right.instance.name)}.{sv_varname(right.io.name)}" + serialize_select(
            right.select
        )

    def _unique_net(self, base: str, net_type: Logic) -> str:
        name = sv_varname(base)
        if name not in self.nets:
            self.nets[name] = net_type
            return name
        idx = 1
        while True:
            cand = sv_varname(f"{base}__{idx}")
            if cand not in self.nets:
                self.nets[cand] = net_type
                return cand
            idx += 1

    def _port_map_or_assign(
        self,
        port: Union[ElaboratableValue, ReferencedPort, str],
        right: Union[ElaboratableValue, ReferencedPort, str],
        invert: bool,
    ) -> None:
        if (
            isinstance(port, ReferencedPort)
            and port.instance is not None
            and port.select.ops == []
            and port.io.name not in self.port_maps[port.instance._id]
        ):
            self.port_maps[port.instance._id][port.io.name] = self._normalize_port_expr(
                ("~" if invert else "") + self._serialize_conn_value(right)
            )
            return
        self.assign_map[self._serialize_conn_value(right)] = (
            "~" if invert else ""
        ) + self._serialize_conn_value(port)

    def _dedupe_partial_selects(
        self,
        selects: list[_SystemVerilogPartialConn],
    ) -> list[_SystemVerilogPartialConn]:
        uniq_selects: list[_SystemVerilogPartialConn] = []
        seen: set[tuple[str, str, bool]] = set()
        for select in selects:
            key = (
                serialize_select(select.select),
                self._serialize_conn_value(select.source),
                select.invert,
            )
            if key in seen:
                continue
            seen.add(key)
            uniq_selects.append(select)
        return uniq_selects

    @staticmethod
    def _is_plain_output_ref(target: Union[ReferencedPort, ElaboratableValue, str]) -> bool:
        return (
            isinstance(target, ReferencedPort)
            and target.instance is not None
            and target.select.ops == []
            and target.io.direction in (PortDirection.OUT, PortDirection.INOUT)
        )

    def _connect_internal_unsliced(
        self,
        instance: ObjectId[ModuleInstance],
        port: Port,
        target: Union[ReferencedPort, ElaboratableValue, str],
        invert: bool,
    ) -> None:
        if not self._is_plain_output_ref(target):
            self._port_map_or_assign(
                ReferencedPort(instance=instance.resolve(), io=port), target, invert
            )
            return
        assert isinstance(target, ReferencedPort)
        src_inst = target.instance
        assert src_inst is not None
        src_port_map = self.port_maps.get(src_inst._id)
        existing = None if src_port_map is None else src_port_map.get(target.io.name)
        self.port_maps[instance][port.name] = ("~" if invert else "") + (
            existing if existing is not None else self._serialize_conn_value(target)
        )

    def _connect_external_unsliced(
        self, port: Port, target: Union[ReferencedPort, ElaboratableValue, str], invert: bool
    ) -> None:
        ext_port_name = sv_varname(port.name)
        if not self._is_plain_output_ref(target):
            self._port_map_or_assign(target, ext_port_name, invert)
            return
        assert isinstance(target, ReferencedPort)
        assert target.instance is not None
        existing = self.port_maps[target.instance._id].get(target.io.name)
        if existing:
            self._port_map_or_assign(existing, ext_port_name, invert)
        else:
            self._port_map_or_assign(target, ext_port_name, invert)

    def _try_direct_partial_connection(
        self,
        instance: Optional[ObjectId[ModuleInstance]],
        port: Port,
        selects: list[_SystemVerilogPartialConn],
    ) -> bool:
        if len(selects) != 1:
            return False
        select, target, invert = selects[0].select, selects[0].source, selects[0].invert
        if select.ops != []:
            return False
        if invert:
            assert isinstance(target, ReferencedPort)

            if not (
                port.direction is PortDirection.IN
                and (target.io.direction is PortDirection.OUT or target.is_external)
            ):
                return False

        if instance is not None:
            self._connect_internal_unsliced(instance, port, target, invert)
        else:
            self._connect_external_unsliced(port, target, invert)
        return True

    def _wire_for_partial_port(
        self, instance: Optional[ObjectId[ModuleInstance]], port: Port, any_inverted: bool
    ) -> str:
        if instance is None and any_inverted:
            wire = sv_varname(f"inv__{port.name}")
            self.nets[wire] = port.type
            self.assign_map[port.name] = wire
            return wire
        if instance is None:
            return sv_varname(port.name)
        wire = sv_varname(f"{instance.resolve().name}__{port.name}")
        self.nets[wire] = port.type
        self.port_maps[instance][port.name] = wire
        return wire

    def _connect_partial_slice(
        self,
        instance: Optional[ObjectId[ModuleInstance]],
        port: Port,
        wire: str,
        partial: _SystemVerilogPartialConn,
    ) -> None:
        wire_slice = wire + serialize_select(partial.select)
        if (instance is None and port.direction is PortDirection.OUT) or (
            instance is not None and port.direction is PortDirection.IN
        ):
            self._port_map_or_assign(partial.source, wire_slice, partial.invert)
            return
        self._port_map_or_assign(wire_slice, partial.source, partial.invert)

    def _parse_partial_conn_entry(
        self,
        instance: Optional[ObjectId[ModuleInstance]],
        port: Port,
        selects: list[_SystemVerilogPartialConn],
    ) -> None:
        deduped = self._dedupe_partial_selects(selects)
        if self._try_direct_partial_connection(instance, port, deduped):
            return
        any_inverted = any(partial.invert for partial in deduped)
        wire = self._wire_for_partial_port(instance, port, any_inverted)
        for partial in deduped:
            self._connect_partial_slice(instance, port, wire, partial)

    def compact_passthrough_nets(self, top_ports: set[str]):
        """
        Collapse trivial top-level passthrough nets of the form:

          <type> tmp;
          assign top_out = tmp;
          u_block (... .out(tmp) ...);

        into direct port mapping:

          u_block (... .out(top_out) ...);
        """

        while True:
            changed = False
            for lhs, rhs in self.assign_map.items():
                if lhs not in top_ports or rhs not in self.nets:
                    continue

                # The passthrough net must not participate in any other assign and can only
                # appear as a direct port-map expression.
                rhs_as_rhs = sum(1 for _l, _r in self.assign_map.items() if _r == rhs)
                rhs_as_lhs = sum(1 for _l in self.assign_map if _l == rhs)
                if rhs_as_rhs != 1 or rhs_as_lhs != 0:
                    continue

                refs: list[tuple[ObjectId[ModuleInstance], str]] = []
                for inst_id, pmap in self.port_maps.items():
                    for pname, expr in pmap.items():
                        if expr == rhs:
                            refs.append((inst_id, pname))
                if not refs:
                    continue

                for inst_id, pname in refs:
                    self.port_maps[inst_id][pname] = lhs
                del self.assign_map[lhs]
                del self.nets[rhs]
                changed = True
                break
            if not changed:
                break


class SystemVerilogDesignBackend:
    template: ClassVar[Template] = get_template("design.j2")

    #: The package from which type and interface definitions
    #: should be imported
    package_name: Optional[str]

    def __init__(self, package_name: Optional[str], all_pins: bool, desc_comms: bool) -> None:
        self.package_name = package_name
        self.all_pins = all_pins
        self.desc_comms = desc_comms

    @staticmethod
    def _expr_mentions_port(expr: str, port_names: set[str]) -> bool:
        for pname in port_names:
            if pname == "":
                continue
            if pname.startswith("\\"):
                if pname in expr:
                    return True
                continue
            if re.search(rf"(?<![A-Za-z0-9_$]){re.escape(pname)}(?![A-Za-z0-9_$])", expr):
                return True
        return False

    def serialize(self, des: Design, *, top_level: bool = True) -> str:
        data = _SystemVerilogDesignData()

        for intf in des.parent.interfaces:
            if intf.has_independent_signals:
                data.intf_exts[sv_varname(intf.name)] = intf.definition

        for conn in des.connections:
            data.parse_connection(conn)
        data.parse_partial_conns()
        data.compact_passthrough_nets({sv_varname(p.name) for p in des.parent.ports})

        if self.all_pins:
            for comp in des.components:
                for io in comp.module.ios:
                    if isinstance(io, Interface) and not io.has_independent_signals:
                        continue
                    if io.name not in data.port_maps[comp._id]:
                        data.port_maps[comp._id][io.name] = ""

        header_params = []
        local_params = []
        port_names = {p.name for p in des.parent.ports}
        for par in des.parent.parameters:
            expr = ""
            if par.default_value is not None:
                expr = str(par.default_value.value)
            if expr != "" and self._expr_mentions_port(expr, port_names):
                local_params.append(par)
            else:
                header_params.append(par)

        out = self.template.render(
            mod=des.parent,
            back=data,
            mod_header_params=header_params,
            mod_local_params=local_params,
            top_level=top_level,
            desc_comms=self.desc_comms,
            package_name=self.package_name,
        )

        return out
