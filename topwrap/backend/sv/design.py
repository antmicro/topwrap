# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import defaultdict
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
from topwrap.model.hdl_types import Logic, LogicSelect
from topwrap.model.interface import Interface, InterfaceDefinition
from topwrap.model.misc import ElaboratableValue, ObjectId
from topwrap.util import MISSING

logger = logging.getLogger(__name__)


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
        list[tuple[LogicSelect, Union[ReferencedPort, ElaboratableValue, str]]],
    ]

    def __init__(self) -> None:
        self.intf_exts = {}
        self.intf_decls = {}
        self.nets = {}
        self.port_maps = defaultdict(dict)
        self.assign_map = {}
        self.conns_to_partials = defaultdict(list)

    def store_sel(self, ref: ReferencedPort, other: Union[ReferencedPort, ElaboratableValue, str]):
        """Shortcut for storing a connection to a slice of an input"""

        i = ref.instance
        self.conns_to_partials[(i if i is None else i._id, ref.io._id)].append((ref.select, other))

    def parse_connection(self, conn: Connection):
        if isinstance(conn, ConstantConnection):
            self.store_sel(conn.target, conn.source)
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
            self.store_sel(conn.source, conn.target)
        else:
            self.store_sel(conn.target, conn.source)

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
                        (ref_port.select, sigref)
                    )

    def parse_partial_conns(self):
        """
        Goes through ``self.conns_to_partials`` in order to update the
        port map, potentially add nets and add entries to the assign map
        """

        def _sright(right: Union[ElaboratableValue, ReferencedPort, str]) -> str:
            """Serialize the right-hand side of an assign statement"""

            if isinstance(right, ReferencedPort):
                if right.instance is None:
                    return sv_varname(right.io.name) + serialize_select(right.select)
                else:
                    return (
                        f"{sv_varname(right.instance.name)}.{sv_varname(right.io.name)}"
                        + serialize_select(right.select)
                    )
            return str(right)

        def _port_map_or_assign(
            port: Union[ElaboratableValue, ReferencedPort, str],
            right: Union[ElaboratableValue, ReferencedPort, str],
        ):
            """
            Connect `port` to `right` through a port map, or if the slot
            in the port map is already taken, through an assign statement
            """

            if (
                isinstance(port, ReferencedPort)
                and port.instance is not None
                and port.select.ops == []
            ):
                if port.io.name not in self.port_maps[port.instance._id]:
                    self.port_maps[port.instance._id][port.io.name] = _sright(right)
            else:
                self.assign_map[_sright(right)] = _sright(port)

        for (instance, port), selects in self.conns_to_partials.items():
            port = port.resolve()

            # if there is only one connection to the entire (unsliced) port
            # we can just put the target directly into the port map
            # without creating any intermediate nets
            if len(selects) == 1:
                select, target = selects[0]
                if select.ops == []:
                    if instance is not None:
                        _port_map_or_assign(
                            ReferencedPort(instance=instance.resolve(), io=port), target
                        )
                    else:
                        _port_map_or_assign(target, sv_varname(port.name))
                    continue

            # if there are any sliced connections, a net is created,
            # its appropriate slices are driven from assigns, and
            # finally the net gets connected in the port map
            if instance is not None:
                wire = f"{sv_varname(instance.resolve().name)}__{port.name}"
                self.nets[wire] = port.type
                self.port_maps[instance][sv_varname(port.name)] = wire
            else:
                wire = sv_varname(port.name)

            for select, right in selects:
                if (
                    instance is None
                    and port.direction is PortDirection.OUT
                    or instance is not None
                    and port.direction is PortDirection.IN
                ):
                    _port_map_or_assign(right, wire + serialize_select(select))
                else:
                    _port_map_or_assign(wire + serialize_select(select), right)


class SystemVerilogDesignBackend:
    template: ClassVar[Template] = get_template("design.j2")

    #: The package from which type and interface definitions
    #: should be imported
    package_name: Optional[str]

    def __init__(self, package_name: Optional[str], all_pins: bool, desc_comms: bool) -> None:
        self.package_name = package_name
        self.all_pins = all_pins
        self.desc_comms = desc_comms

    def serialize(self, des: Design, *, top_level: bool = True) -> str:
        data = _SystemVerilogDesignData()

        for intf in des.parent.interfaces:
            if intf.has_independent_signals:
                data.intf_exts[sv_varname(intf.name)] = intf.definition

        for conn in des.connections:
            data.parse_connection(conn)
        data.parse_partial_conns()

        if self.all_pins:
            for comp in des.components:
                for io in comp.module.ios:
                    if isinstance(io, Interface) and not io.has_independent_signals:
                        continue
                    if io.name not in data.port_maps[comp._id]:
                        data.port_maps[comp._id][io.name] = ""

        out = self.template.render(
            mod=des.parent,
            back=data,
            top_level=top_level,
            desc_comms=self.desc_comms,
            package_name=self.package_name,
        )

        return out
