# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC
from dataclasses import field
from typing import TYPE_CHECKING, Generic, Mapping

import marshmallow_dataclass
from typing_extensions import TypeVar

from topwrap.common_serdes import MarshmallowDataclassExtensions
from topwrap.model.connections import ReferencedInterface, ReferencedPort
from topwrap.model.misc import ElaboratableValue, ObjectId, VariableName

if TYPE_CHECKING:
    from topwrap.model.module import Design


@marshmallow_dataclass.dataclass
class InterconnectParams(MarshmallowDataclassExtensions):
    """Base class for parameters/settings specific to a concrete interconnect type"""


@marshmallow_dataclass.dataclass
class InterconnectManagerParams(MarshmallowDataclassExtensions):
    """Base class for manager parameters specific to a concrete interconnect type"""


@marshmallow_dataclass.dataclass
class InterconnectSubordinateParams(MarshmallowDataclassExtensions):
    """
    Base class for subordinate parameters specific to a concrete interconnect type.

    Transactions to addresses in range [self.address; self.address + self.size)
    will be routed to this subordinate.
    """

    #: The start address of this subordinate in the memory map
    address: ElaboratableValue.Field = field(default_factory=lambda: ElaboratableValue(0))

    #: The size in bytes of this subordinate's address space
    size: ElaboratableValue.Field = field(default_factory=lambda: ElaboratableValue(0))


_MANPAR = TypeVar(
    "_MANPAR", bound=InterconnectManagerParams, default=InterconnectManagerParams, covariant=True
)
_SUBPAR = TypeVar(
    "_SUBPAR",
    bound=InterconnectSubordinateParams,
    default=InterconnectSubordinateParams,
    covariant=True,
)
_IPAR = TypeVar("_IPAR", bound=InterconnectParams, default=InterconnectParams, covariant=True)


class Interconnect(ABC, Generic[_IPAR, _MANPAR, _SUBPAR]):
    """
    Base class for multiple interconnect generator implementations.

    Interconnects connect multiple interface instances together in
    a many-to-many topology, combining multiple subordinates into
    a unified address space so that one or multiple managers can
    access them.
    """

    name: VariableName

    #: The design containing this interconnect
    parent: Design

    #: The clock signal for this interconnect
    clock: ReferencedPort

    #: The reset signal for this interconnect
    reset: ReferencedPort

    #: Interconnect-wide type-specific parameters
    params: _IPAR

    #: Manager interfaces controlling this interconnect
    #: described as a mapping between a referenced interface
    #: in a design and the type-specific manager configuration
    managers: dict[ObjectId[ReferencedInterface], _MANPAR]

    #: Subordinate interfaces subject to this interconnect
    #: described in the same format as managers
    subordinates: dict[ObjectId[ReferencedInterface], _SUBPAR]

    def __init__(
        self,
        *,
        name: str,
        clock: ReferencedPort,
        reset: ReferencedPort,
        params: _IPAR,
        managers: Mapping[ObjectId[ReferencedInterface], _MANPAR] = {},
        subordinates: Mapping[ObjectId[ReferencedInterface], _SUBPAR] = {},
    ):
        self.name = name
        self.clock = clock
        self.reset = reset
        self.params = params
        self.managers = dict(managers)
        self.subordinates = dict(subordinates)
