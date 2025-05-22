# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import reduce
from typing import Generic, Optional, TypeVar, Union

from topwrap.model.misc import ElaboratableValue, VariableName, set_parent


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

    #: The parent of this type. Used to create a reference tree
    #: between complex type definitions, for example between ``LogicArray``
    #: and the inner type it contains or between a ``BitStruct`` and its fields.
    #: Is ``None`` when this represents a top-level type
    parent: Optional[Logic]

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__()
        self.name = name

    @property
    @abstractmethod
    def size(self) -> ElaboratableValue:
        """All ``Logic`` subclasses should have an elaboratable size (the number of bits)"""


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

    def __init__(
        self, *, name: Optional[str] = None, dimensions: list[Dimensions], item: _ArrayItemOrField
    ):
        """
        Constructs the array type

        :param dimensions: A list of dimensions of the array.
            E.g. A ``logic[7:0][31:0]`` type has ``[(7:0), (31:0)]`` dimensions.
        """

        super().__init__(name)
        self.dimensions = dimensions
        self.item = item
        set_parent(item, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, LogicArray):
            return self.dimensions == value.dimensions and self.item == value.item
        return NotImplemented


class Bits(LogicArray[Bit]):
    """A multidimensional array of bits"""

    def __init__(self, *, name: Optional[str] = None, dimensions: list[Dimensions]):
        super().__init__(dimensions=dimensions, item=Bit(), name=name)


class StructField(Logic, Generic[_ArrayItemOrField]):
    """A field in a ``BitStruct``"""

    type: _ArrayItemOrField
    field_name: VariableName

    @property
    def size(self):
        return self.type.size

    def __init__(self, *, name: VariableName, type: _ArrayItemOrField) -> None:
        super().__init__()
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

    def __init__(self, *, name: Optional[str] = None, fields: list[StructField[Logic]]) -> None:
        super().__init__(name)
        self.fields = fields
        for f in fields:
            set_parent(f.type, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, BitStruct):
            return self.fields == value.fields
        return NotImplemented


@dataclass
class LogicSelect:
    """
    Represents an arbitrary selection of a part of a logical type.
    For example if ``self.logic`` references a multidimensional
    ``LogicArray``, then you could have multiple ``LogicBitSelect``
    operations in ``self.ops`` to select an arbitrary bit from that slice.
    Similarly, if there's a structure somewhere in the path you can add
    ``LogicFieldSelect`` to the operations to subscribe a specific logical field.
    """

    logic: Logic
    ops: list[Union[LogicFieldSelect, LogicBitSelect]] = field(default_factory=list)


@dataclass
class LogicFieldSelect:
    """Represents access operation to a field of a structure"""

    field: StructField[Logic]


@dataclass
class LogicBitSelect:
    """Represents a logic array indexing operation"""

    slice: Dimensions
