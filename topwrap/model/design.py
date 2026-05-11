# Copyright (c) 2024-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, Iterator, Mapping, Optional, Union

from topwrap.model.connections import (
    Clock,
    Connection,
    InterfaceConnection,
    PortConnection,
    ReferencedInterface,
    ReferencedIO,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.interconnect import Interconnect, InterconnectSubordinateParams
from topwrap.model.memory_map import MemoryMap
from topwrap.model.misc import (
    ElaboratableValue,
    ModelBase,
    ObjectId,
    Parameter,
    QuerableView,
    VariableName,
    set_parent,
)

if TYPE_CHECKING:
    from topwrap.model.module import Module


logger = logging.getLogger(__name__)


class ModuleInstance(ModelBase):
    """
    Represents an instantiated module with values supplied for
    its appropriate respective parameters. This class is necessary
    to differentiate multiple instances of the same module in a design.
    """

    #: The name of this instance. It corresponds to "instance_name" in
    #: this exemplary Verilog construct:
    #: ``MODULE #(.WIDTH(32)) instance_name (.clk(clk));``
    name: VariableName

    #: The module that this is an instance of. Corresponds to "MODULE" in
    #: the Verilog construct defined above.
    module: Module

    #: Concrete parameter values for the module that this is an instance of.
    #: Corresponds to "#(.WIDTH(32))" in the above Verilog construct.
    parameters: dict[ObjectId[Parameter], ElaboratableValue]

    #: Assignments between this instance's clock inputs and clock domains.
    clocks: dict[ObjectId[Clock], ClockDomain]

    #: Assignments between this instance's reset inputs and reset domains.
    resets: dict[ObjectId[Reset], ResetDomain]

    #: Reference to the design that contains this component
    parent: Design

    def __init__(
        self,
        *,
        name: VariableName,
        module: Module,
        parameters: Mapping[ObjectId[Parameter], ElaboratableValue] = {},
        clocks: Mapping[ObjectId[Clock], ClockDomain] = {},
        resets: Mapping[ObjectId[Reset], ResetDomain] = {},
    ) -> None:
        super().__init__()
        self.name = name
        self.module = module
        self.parameters = {}
        self.clocks = {}
        self.resets = {}
        self.parameters.update(parameters)
        self.clocks.update(clocks)
        self.resets.update(resets)


class ClockDomain(ModelBase):
    """This class represents a clock domain defined within a design."""

    name: VariableName

    #: Reference to a port acting as the source for this clock domain.
    clock: ReferencedPort

    #: Reference to the design that contains this clock domain.
    parent: Design

    def __init__(self, *, name: str, clock: ReferencedPort):
        super().__init__()
        self.name = name
        self.clock = clock


class ResetDomain(ModelBase):
    """This class represents a reset domain defined within a design."""

    name: VariableName

    #: Reference to a port acting as the source for this reset domain.
    reset: ReferencedPort

    #: Polarity of the reset signal.
    polarity: ResetPolarity

    #: Clock domain to which this reset domain is synchronous to.
    #: ``None`` if the reset signal is asynchronous.
    synchronous_to: Optional[ClockDomain]

    #: Reference to the design that contains this reset domain.
    parent: Design

    def __init__(
        self,
        *,
        name: str,
        reset: ReferencedPort,
        polarity: ResetPolarity,
        synchronous_to: Optional[ClockDomain] = None,
    ):
        super().__init__()
        self.name = name
        self.reset = reset
        self.polarity = polarity
        self.synchronous_to = synchronous_to


class DesignDomainException(Exception):
    """Error relating to clock and reset domains within a design."""

    pass


class Design(ModelBase):
    """
    This class represents the inner block design of a specific ``Module``.
    It consists of instances of other modules (components) and connections between
    them, each other, and external ports of the module that this design represents.
    """

    _components: list[ModuleInstance]
    _interconnects: list[Interconnect]
    _connections: list[Connection]
    _clock_domains: list[ClockDomain]
    _reset_domains: list[ResetDomain]
    memory_maps: dict[str, MemoryMap]
    parent: Module

    def __init__(
        self,
        *,
        components: Iterable[ModuleInstance] = (),
        interconnects: Iterable[Interconnect] = (),
        connections: Iterable[Connection] = (),
        clock_domains: Iterable[ClockDomain] = (),
        reset_domains: Iterable[ResetDomain] = (),
        memory_maps: Optional[dict[str, MemoryMap]] = None,
    ) -> None:
        super().__init__()
        self._components = []
        self._interconnects = []
        self._connections = []
        self._clock_domains = []
        self._reset_domains = []
        self.memory_maps = {}

        if memory_maps is not None:
            self.add_memory_maps(memory_maps)
        for component in components:
            self.add_component(component)
        for intercon in interconnects:
            self.add_interconnect(intercon)
        for conn in connections:
            self.add_connection(conn)
        for domain in clock_domains:
            self.add_clock_domain(domain)
        for domain in reset_domains:
            self.add_reset_domain(domain)

    @property
    def components(self) -> QuerableView[ModuleInstance]:
        return QuerableView(self._components)

    @property
    def interconnects(self) -> QuerableView[Interconnect]:
        return QuerableView(self._interconnects)

    @property
    def connections(self) -> QuerableView[Connection]:
        return QuerableView(self._connections)

    @property
    def clock_domains(self) -> QuerableView[ClockDomain]:
        return QuerableView(self._clock_domains)

    @property
    def reset_domains(self) -> QuerableView[ResetDomain]:
        return QuerableView(self._reset_domains)

    def add_component(self, component: ModuleInstance):
        set_parent(component, self)
        self._components.append(component)

    def add_interconnect(self, interconnect: Interconnect):
        set_parent(interconnect, self)
        self._interconnects.append(interconnect)

    def add_connection(self, connection: Connection):
        set_parent(connection, self)
        self._connections.append(connection)

    def add_clock_domain(self, domain: ClockDomain):
        set_parent(domain, self)
        self._clock_domains.append(domain)

    def add_reset_domain(self, domain: ResetDomain):
        set_parent(domain, self)
        self._reset_domains.append(domain)

    def add_memory_maps(self, mem_maps: dict[str, MemoryMap]):
        for memory_map in mem_maps.values():
            memory_map.parent = self
        self.memory_maps.update(mem_maps)

    def connections_with(
        self, io: ReferencedIO
    ) -> Iterator[Union[ElaboratableValue, ReferencedIO]]:
        """
        Yields everything that is connected to a given IO.

        :param io: The IO of which connections to yield.
        """

        for conn in self.connections:
            if isinstance(io, ReferencedPort):
                if isinstance(conn.source, ReferencedPort) and io.overlaps(conn.source):
                    yield conn.target
                elif isinstance(conn.target, ReferencedPort) and io.overlaps(conn.target):
                    yield conn.source
            elif conn.source == io:
                yield conn.target
            elif conn.target == io:
                yield conn.source

    def lower_domains(self):
        """
        Lower clock/reset domain assignments into regular port connections.
        """

        def _ref_port_str(ref: ReferencedPort) -> str:
            if ref.external:
                return f"external port {ref.io.name}"
            else:
                assert ref.instance is not None
                return f"port {ref.instance.name}.{ref.io.name}"

        for comp in self.components:
            # Create clock connections
            for clock in comp.module.clocks:
                clock_dom = comp.clocks[clock._id]

                logger.info(
                    f"Connecting clock '{clock.name}' of module '{comp.name}' to "
                    f"clock domain '{clock_dom.name}' "
                    f"({_ref_port_str(clock_dom.clock)} to "
                    f"port {comp.name}.{clock.clock.name})"
                )

                self.add_connection(
                    PortConnection(
                        source=clock_dom.clock,
                        target=ReferencedPort(io=clock.clock, instance=comp),
                    )
                )

            # Create reset connections
            for reset in comp.module.resets:
                reset_dom = comp.resets[reset._id]

                invert = reset_dom.polarity is not reset.polarity

                # TODO: Insert synchronizer
                if reset.synchronous_to is not None and reset_dom.synchronous_to is None:
                    raise DesignDomainException(
                        f"Reset '{reset.name}', which is synchronous to clock "
                        f"'{reset.synchronous_to.clock}' is connected to "
                        f"asynchronous reset domain '{reset_dom.name}'"
                    )

                if reset.synchronous_to is not None and (
                    comp.clocks[reset.synchronous_to._id] != reset_dom.synchronous_to
                ):
                    assert reset_dom.synchronous_to

                    raise DesignDomainException(
                        f"Reset '{reset.name}', which is synchronous to clock domain "
                        f"'{comp.clocks[reset.synchronous_to._id].name}' is connected to "
                        f"reset domain '{reset_dom.name}', which is synchronous to "
                        f"clock domain '{reset_dom.synchronous_to.name}'"
                    )

                invert_msg = "(inverted due to polarity)" if invert else ""
                logger.info(
                    f"Connecting reset '{reset.name}' of module '{comp.name}' to "
                    f"reset domain '{reset_dom.name}' "
                    f"({_ref_port_str(reset_dom.reset)} to "
                    f"port {comp.name}.{reset.reset.name}) {invert_msg}"
                )

                self.add_connection(
                    PortConnection(
                        source=reset_dom.reset,
                        target=ReferencedPort(io=reset.reset, instance=comp),
                        invert=invert,
                    )
                )

            self.check_intf_cdc()

    def check_intf_cdc(self):
        # Check if any interface connections need CDC
        for conn in self.connections:
            if not isinstance(conn, InterfaceConnection):
                continue

            def _inst(ref: ReferencedInterface) -> str:
                return (
                    f"from instance '{ref.instance.name}'"
                    if ref.instance is not None
                    else "external"
                )

            src_io, tgt_io = conn.source.io, conn.target.io
            src_clk, tgt_clk = src_io.clock, tgt_io.clock
            src_inst, tgt_inst = _inst(conn.source), _inst(conn.target)

            # If no clocks are known, ignore this connection.
            if src_clk is None and tgt_clk is None:
                continue

            # If one side has a clock and the other doesn't, issue a warning.
            if (src_clk is None) != (tgt_clk is None):
                logger.warning(
                    f"Connection between interface '{src_io.name}' ({src_inst}) "
                    f"and interface '{tgt_io.name}' ({tgt_inst}) cannot be checked for "
                    "CDC: one of the interfaces does not have clock information."
                )
                continue

            assert src_clk is not None and tgt_clk is not None

            # TODO: Currently this holds, since there is no way to reasonably attach clocks to
            # external interfaces. This should probably be changed though.
            assert conn.source.instance is not None and conn.target.instance is not None

            src_domain = conn.source.instance.clocks.get(src_clk._id)
            assert src_domain is not None
            tgt_domain = conn.target.instance.clocks.get(tgt_clk._id)
            assert tgt_domain is not None

            if src_domain != tgt_domain:
                # TODO: Insert a CDC block between the two sides of the connection if possible
                raise DesignDomainException(
                    f"Connection between interface '{src_io.name}' ({src_inst}) "
                    f"and interface '{tgt_io.name}' ({tgt_inst}) crosses clock domains: "
                    f"former is driven by domain '{src_domain.name}', while "
                    f"latter is driven by domain '{tgt_domain.name}'."
                )

    def update_interconnects_from_memory_maps(self):
        for interconnect in self._interconnects:
            if interconnect.memory_map:
                for addr, entry in interconnect.memory_map.map.items():
                    iface = entry.ref_iface
                    size = None
                    # First check in module.yaml
                    if iface.io.size is not None:
                        size = iface.io.size
                    # Then check in design.yaml and overwrite if present
                    if "size" in entry.parameters:
                        size = entry.parameters["size"]
                    if size is None:
                        raise Exception(
                            f"interface '{iface.instance.name}.{iface.io.name}' in "
                            f"'{interconnect.memory_map.name}' address map don't have defines "
                            "size in design.yaml or module.yaml"
                        )
                    subordinate = InterconnectSubordinateParams(
                        address=ElaboratableValue(addr), size=ElaboratableValue(size)
                    )
                    interconnect.subordinates[iface._id] = subordinate
