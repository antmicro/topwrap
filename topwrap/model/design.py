# Copyright (c) 2024-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Iterator, Mapping, Optional, Union

from topwrap.model.connections import (
    Clock,
    Connection,
    ReferencedIO,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.interconnect import Interconnect
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
    parent: Module

    def __init__(
        self,
        *,
        components: Iterable[ModuleInstance] = (),
        interconnects: Iterable[Interconnect] = (),
        connections: Iterable[Connection] = (),
        clock_domains: Iterable[ClockDomain] = (),
        reset_domains: Iterable[ResetDomain] = (),
    ) -> None:
        super().__init__()
        self._components = []
        self._interconnects = []
        self._connections = []
        self._clock_domains = []
        self._reset_domains = []

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
