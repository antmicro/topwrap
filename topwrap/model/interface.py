# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Iterable, Iterator, Mapping, Optional

from topwrap.model.connections import PortDirection, ReferencedPort
from topwrap.model.hdl_types import Logic
from topwrap.model.misc import (
    ElaboratableValue,
    Identifier,
    ModelBase,
    ObjectId,
    QuerableView,
    VariableName,
    set_parent,
)

if TYPE_CHECKING:
    from topwrap.model.module import Module


class InterfaceMode(Enum):
    MANAGER = "manager"
    SUBORDINATE = "subordinate"
    UNSPECIFIED = "unspecified"


@dataclass
class InterfaceSignalConfiguration:
    """Holds the mode-specific configuration of an interface signal"""

    #: The direction of this signal in a given ``InterfaceMode``
    direction: PortDirection

    #: Whether this signal is required or optional
    required: bool


class InterfaceSignal(ModelBase):
    """
    This class represents a signal in an interface definition.
    E.g.: The ``awaddr`` signal in the AXI interface etc.
    """

    name: VariableName

    #: While automatically deducing interfaces, if an arbitrary signal's
    #: name matches this regular expression then that signal is considered
    #: as a candidate for realizing this signal definition
    regexp: re.Pattern[str]

    #: A dictionary of modes for this signal and their specific configurations
    #: E.g.: A signal that only has an ``InterfaceMode.MANAGER`` entry in this
    #: dictionary means that it's valid only on the manager's side.
    modes: dict[InterfaceMode, InterfaceSignalConfiguration]

    #: The logical type of this signal. Fulfills the same function as ``Port.type``
    type: Logic

    #: The default value for this signal, if any
    default: Optional[ElaboratableValue] = None

    #: The definition that this signal belongs to
    parent: InterfaceDefinition

    def __init__(
        self,
        *,
        name: VariableName,
        regexp: re.Pattern[str],
        type: Logic,
        default: Optional[ElaboratableValue] = None,
        modes: Optional[Mapping[InterfaceMode, InterfaceSignalConfiguration]] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.regexp = regexp
        self.type = type
        self.default = default
        self.modes = {}
        self.modes.update({} if modes is None else modes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, InterfaceSignal):
            return (
                self.name == value.name
                and self.modes == value.modes
                and self.regexp == value.regexp
            )
        return NotImplemented


class InterfaceDefinition(ModelBase):
    """This represents a definition of an entire interface/bus. E.g. AXI, AHB, Wishbone, etc."""

    id: Identifier
    _signals: list[InterfaceSignal]

    def __init__(self, *, id: Identifier, signals: Iterable[InterfaceSignal] = ()) -> None:
        super().__init__()
        self.id = id
        self._signals = [*signals]

    @property
    def signals(self) -> QuerableView[InterfaceSignal]:
        """
        A list of signal definitions that make up this interface
        E.g. awaddr, araddr, wdata, rdata, etc.... in AXI
        """
        return QuerableView(self._signals)

    def add_signal(self, signal: InterfaceSignal):
        set_parent(signal, self)
        self._signals.append(signal)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, InterfaceDefinition):
            return (
                self.id == value.id
                and all(s in self.signals for s in value.signals)
                and all(s in value.signals for s in self.signals)
            )
        return NotImplemented


@dataclass
class Interface:
    """
    A realised instance of an interface that can be connected with other
    interface instances through ``InterfaceConnection``.

    The relationship between this class and ``InterfaceDefinition`` is similar to
    the relationship between ``ModuleInstance`` and ``Module`` classes.
    """

    #: Name for this interface instance
    name: VariableName

    #: The mode of this instance (e.g. manager/subordinate)
    mode: InterfaceMode

    #: The definition of the interface that this is an instance of
    definition: InterfaceDefinition

    #: The module definition that contains this interface instance
    parent: Module = field(init=False, compare=False)

    #: Realization of signals defined in this interface.
    #: A signal can be realized either by:
    #:
    #: - Slicing an already existing external port of
    #:   the module that this instance belongs to (self.parent), in that case
    #:   the value in this dictionary is the aforementioned port reference.
    #:
    #: - Independently, meaning that whenever necessary, e.g. during
    #:   output generation by a ``Backend`` that does not support interfaces,
    #:   an arbitrarily generated port based on the ``InterfaceSignal.type``
    #:   should be generated to represent it. In that case the value in this
    #:   dictionary is ``None``.
    #:
    #: If an entry for a specific signal that exists in the definition is not
    #: present in this dictionary, then that signal will not be realized at all.
    #: E.g. when it was configured as optional or was given a default value in
    #: ``InterfaceSignalConfiguration``.
    signals: Mapping[ObjectId[InterfaceSignal], Optional[ReferencedPort]] = field(
        default_factory=dict
    )

    @property
    def independent_signals(self) -> Iterator[InterfaceSignal]:
        """Yields signals that are not realized by any external ports of the Module"""

        yield from (s.resolve() for s, v in self.signals.items() if v is None)

    @property
    def sliced_signals(self) -> Iterator[tuple[InterfaceSignal, ReferencedPort]]:
        """Yields signals that are realized by external ports of the Module"""

        yield from ((s.resolve(), v) for s, v in self.signals.items() if v is not None)

    @property
    def has_independent_signals(self) -> bool:
        return next(self.independent_signals, None) is not None

    @property
    def has_sliced_signals(self) -> bool:
        return next(self.sliced_signals, None) is not None
