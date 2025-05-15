# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import reduce
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union

from topwrap.model.misc import ElaboratableValue, VariableName, set_parent

if TYPE_CHECKING:
    from topwrap.model.connections import Port
    from topwrap.model.interface import InterfaceSignal


@dataclass
class Dimensions:
    """
    A pair of values representing bounds for a single dimension of a Logic type.
    Verilog examples:
    -   ``logic`` -> upper == lower == 0
    -   ``logic[31:0]`` -> upper == 31, lower == 0
    -   ``logic[0:64]`` -> upper == 0, lower == 64
    """

    upper: ElaboratableValue = field(default_factory=lambda: ElaboratableValue("0"))
    lower: ElaboratableValue = field(default_factory=lambda: ElaboratableValue("0"))


class Logic(ABC):
    """
    An abstract class representing anything that can be used as
    a logical type for a port or a signal in a module.
    """

    name: Optional[VariableName]

    #: The parent of this type. Can be either:
    #:
    #: - ``Logic`` - e.g. if this is a ``StructField`` then its parent would be a
    #:      `BitStruct`.
    #:
    #: - ``Port`` or ``InterfaceSignal`` - in case this represents a top-level
    #:      type definition for an IO.
    #:
    #: - ``None`` - in case this is a standalone top-level type definition (e.g. ``typedef struct``)
    parent: Optional[Union[Logic, Port, InterfaceSignal]]

    @property
    @abstractmethod
    def size(self) -> ElaboratableValue:
        """All ``Logic`` subclasses should have an elaboratable size (the number of bits)"""

    @property
    def outer(self) -> Optional[Union[Port, InterfaceSignal]]:
        """
        Recursively traverses through parents and returns the IO
        definition that uses this type if encountered.
        """

        visited = set()
        target = self
        while isinstance(target, Logic):
            if (idd := id(target)) in visited:
                return None
            visited.add(idd)
            target = self.parent
        return target


class LogicSlice:
    """Represents a slicing operation on a logical type"""

    logic: Logic
    _upper: Optional[ElaboratableValue]
    _lower: Optional[ElaboratableValue]

    @property
    def upper(self) -> ElaboratableValue:
        """Upper bound of the slice"""
        return self.logic.size if self._upper is None else self._upper

    @upper.setter
    def upper(self, value: Optional[ElaboratableValue]):
        self._upper = value

    @property
    def lower(self) -> ElaboratableValue:
        """Lower bound of the slice"""
        return ElaboratableValue(0) if self._lower is None else self._lower

    @lower.setter
    def lower(self, value: Optional[ElaboratableValue]):
        self._lower = value

    def __init__(
        self,
        *,
        logic: Logic,
        upper: Optional[ElaboratableValue] = None,
        lower: Optional[ElaboratableValue] = None,
    ) -> None:
        self.logic = logic
        self.upper = upper
        self.lower = lower

    def __eq__(self, value: object) -> bool:
        if isinstance(value, LogicSlice):
            return (
                self.upper == value.upper
                and self.lower == value.lower
                and self.logic == value.logic
                and self.logic.outer == value.logic.outer
            )
        return NotImplemented


class Bit(Logic):
    """A single bit type. Equivalent to ``logic`` or ``logic[0:0]`` type in Verilog."""

    @property
    def size(self) -> ElaboratableValue:
        return ElaboratableValue(1)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Bit):
            return True
        return NotImplemented


_ArrayItemOrField = TypeVar("_ArrayItemOrField", bound=Logic)


class LogicArray(Logic, Generic[_ArrayItemOrField]):
    """A type representing a multidimensional array of logical elements."""

    dimensions: list[Dimensions]
    item: _ArrayItemOrField

    @property
    def size(self):
        return self.item.size * reduce(
            lambda a, b: (b.upper - b.lower) * a, self.dimensions, ElaboratableValue(0)
        )

    def __init__(self, *, dimensions: list[Dimensions], item: _ArrayItemOrField):
        """
        Constructs the array type

        :param dimensions: A list of dimensions of the array.
            E.g. A ``logic[7:0][31:0]`` type has ``[(7:0), (31:0)]`` dimensions.
        """

        super().__init__()
        self.dimensions = dimensions
        self.item = item
        set_parent(item, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, LogicArray):
            return self.dimensions == value.dimensions and self.item == value.item
        return NotImplemented


class Bits(LogicArray[Bit]):
    """A multidimensional array of bits"""

    def __init__(self, *, dimensions: list[Dimensions]):
        super().__init__(dimensions=dimensions, item=Bit())


class StructField(Logic, Generic[_ArrayItemOrField]):
    """A field in a ``BitStruct``"""

    type: _ArrayItemOrField
    field_name: VariableName

    @property
    def size(self):
        return self.type.size

    def __init__(self, *, name: VariableName, type: _ArrayItemOrField) -> None:
        self.name = self.field_name = name
        self.type = type

    def __eq__(self, value: object) -> bool:
        if isinstance(value, StructField):
            return self.name == value.name and self.type == value.type
        return NotImplemented


class BitStruct(Logic):
    """A complex structural type equivalent to a ``struct {...}`` construct in SystemVerilog."""

    fields: list[StructField[Logic]]

    @property
    def size(self):
        return reduce(lambda a, b: a + b.type.size, self.fields, ElaboratableValue(0))

    def __init__(self, *, fields: list[StructField[Logic]]) -> None:
        super().__init__()
        self.fields = fields
        for f in fields:
            set_parent(f.type, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, BitStruct):
            return self.fields == value.fields
        return NotImplemented
