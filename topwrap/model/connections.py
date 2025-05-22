# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union

from topwrap.model.hdl_types import Bit, Logic, LogicSelect
from topwrap.model.misc import ElaboratableValue, ModelBase, VariableName

if TYPE_CHECKING:
    from topwrap.model.design import Design, ModuleInstance
    from topwrap.model.interface import Interface  # noqa: F401
    from topwrap.model.module import Module


class PortDirection(Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"


class Port:
    """
    This represents an external port of a HDL module that can
    be connected to other ports or constant values in a design.
    """

    name: VariableName
    direction: PortDirection

    #: The module definition that exposes this port
    parent: Module

    #: The type of this port. (``Bit``, ``BitStruct``, ``LogicArray`` etc.)
    type: Logic

    def __init__(
        self, *, name: VariableName, direction: PortDirection, type: Optional[Logic] = None
    ):
        super().__init__()
        self.name = name
        self.direction = direction
        self.type = Bit() if type is None else type

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Port):
            return (
                self.name == value.name
                and self.direction == value.direction
                and self.type == value.type
            )
        return NotImplemented


_REFIO = TypeVar("_REFIO")


class _ReferencedIO(ModelBase, ABC, Generic[_REFIO]):
    """
    This class represents an association between an IO-like type
    (e.g. an ``Interface`` or a slice of a ``Port``) and
    the concrete component to which that IO belongs. The IO object
    was defined at the level of a module definition (``Module``) so this class
    is necessary to differentiate among IOs of multiple module instances in a design.
    """

    instance: Optional[ModuleInstance]
    io: _REFIO

    def __init__(self, *, instance: Optional[ModuleInstance] = None, io: _REFIO) -> None:
        super().__init__()
        self.instance = instance
        self.io = io

    @property
    def is_external(self):
        """
        ``True`` if this IO reference represents the top-level IO of a module,
        as opposed to a reference to IO of an inner component in a design.
        """

        return self.instance is None

    @classmethod
    def external(cls, io: _REFIO):
        """A shortcut constructor for a reference to a top-level IO of the current module"""

        return cls(instance=None, io=io)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, _ReferencedIO):
            return self.instance == value.instance and self.io == value.io
        return NotImplemented


class ReferencedPort(_ReferencedIO[Port]):
    """Represents a correctly typed reference to a port"""

    select: LogicSelect

    def __init__(
        self,
        *,
        instance: Optional[ModuleInstance] = None,
        io: Port,
        select: Optional[LogicSelect] = None,
    ) -> None:
        super().__init__(instance=instance, io=io)
        self.select = LogicSelect(io.type, []) if select is None else select

    @classmethod
    def external(cls, io: Port, select: Optional[LogicSelect] = None):
        """A shortcut constructor for a reference to a top-level IO of the current module"""

        return cls(instance=None, io=io, select=select)


class ReferencedInterface(_ReferencedIO["Interface"]):
    """Represents a correctly typed reference to an interface"""


ReferencedIO = Union[ReferencedPort, ReferencedInterface]


_SRC = TypeVar("_SRC")
_TRG = TypeVar("_TRG")


@dataclass
class _Connection(ABC, Generic[_SRC, _TRG]):
    """Represents a connection between two IO-like types"""

    source: _SRC
    target: _TRG
    parent: Design = field(init=False, compare=False)


class ConstantConnection(_Connection[ElaboratableValue, ReferencedPort]):
    """Represents a connection between a constant value and a port of a component"""


class PortConnection(_Connection[ReferencedPort, ReferencedPort]):
    "Represents a connection between two ports of some components"


class InterfaceConnection(_Connection[ReferencedInterface, ReferencedInterface]):
    "Represents a connection between two interfaces of some components"


Connection = Union[ConstantConnection, PortConnection, InterfaceConnection]
