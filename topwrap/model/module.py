# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import deque
from typing import Iterable, Iterator, Optional, Union

from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.interface import Interface
from topwrap.model.misc import (
    FileReference,
    Identifier,
    ModelBase,
    Parameter,
    QuerableView,
    set_parent,
)


class Module(ModelBase):
    """
    The top-level class of the IR. It fully represents
    the public interface of a HDL module, holding definitions of all of its
    structured ports and interfaces, parameters, and optionally its inner
    block design if available.
    """

    id: Identifier

    _refs: list[FileReference]
    _ports: list[Port]
    _parameters: list[Parameter]
    _interfaces: list[Interface]
    _design: Optional[Design]

    def __init__(
        self,
        *,
        id: Identifier,
        refs: Iterable[FileReference] = (),
        ports: Iterable[Port] = (),
        parameters: Iterable[Parameter] = (),
        interfaces: Iterable[Interface] = (),
        design: Optional[Design] = None,
    ) -> None:
        super().__init__()
        self.id = id
        self._refs = []
        self._ports = []
        self._parameters = []
        self._interfaces = []
        self._design = None

        for port in ports:
            self.add_port(port)
        for param in parameters:
            self.add_parameter(param)
        for intf in interfaces:
            self.add_interface(intf)
        for ref in refs:
            self.add_reference(ref)
        self.design = design

    @property
    def design(self):
        """Returns the optional inner block design of this module"""
        return self._design

    @design.setter
    def design(self, des: Optional[Design]):
        if des:
            set_parent(des, self)
        self._design = des

    @property
    def ports(self) -> QuerableView[Port]:
        return QuerableView(self._ports)

    @property
    def parameters(self) -> QuerableView[Parameter]:
        return QuerableView(self._parameters)

    @property
    def interfaces(self) -> QuerableView[Interface]:
        return QuerableView(self._interfaces)

    @property
    def ios(self) -> QuerableView[Union[Port, Interface]]:
        """Returns a combined view on both ports and interfaces"""

        return QuerableView(self._ports, self._interfaces)

    @property
    def refs(self) -> QuerableView[FileReference]:
        """
        Returns references to external files that define this module, if any.
        This information is generally added by the respective frontend used to parse this module.
        """

        return QuerableView(self._refs)

    def add_port(self, port: Port):
        set_parent(port, self)
        self._ports.append(port)

    def add_parameter(self, parameter: Parameter):
        set_parent(parameter, self)
        self._parameters.append(parameter)

    def add_interface(self, interface: Interface):
        set_parent(interface, self)
        self._interfaces.append(interface)

    def add_reference(self, ref: FileReference):
        self._refs.append(ref)

    def non_intf_ports(self) -> Iterator[Port]:
        """Yield ports that don't realise signals of any interface"""

        used_ports = [
            sig.io
            for intf in self.interfaces
            for sig in intf.signals.values()
            if sig is not None and sig.io is not None
        ]

        return (port for port in self.ports if port not in used_ports)

    def hierarchy(self: Module) -> QuerableView[Module]:
        """
        Traverses the entire hierarchy tree of this module
        in order, using a BFS algorithm. Returns every unique
        module encountered on the way. The result also includes
        the current module.
        """

        hier = []
        visited = {self._id}
        queue = deque([self])
        while len(queue) > 0:
            target = queue.popleft()
            hier.append(target)
            if target.design is not None:
                for comp in target.design.components:
                    if comp.module._id not in visited:
                        visited.add(comp.module._id)
                        queue.append(comp.module)

        return QuerableView(hier)
