# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from functools import reduce
from itertools import zip_longest
from math import ceil, log2
from typing import (
    Collection,
    Generic,
    Iterable,
    Mapping,
    Optional,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import override

from topwrap.model.misc import ElaboratableValue, ModelBase, VariableName, set_parent


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

    @classmethod
    def single(cls, val: ElaboratableValue):
        return cls(upper=val, lower=val)


class Logic(ModelBase, ABC):
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

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Logic):
            return self.name == value.name
        return NotImplemented

    @abstractmethod
    def copy(self) -> Logic:
        """
        Clones the Logic type in a way to create two separate object trees,
        so that a deeper modification to one tree is not be reflected in
        the other.
        """

    @property
    @abstractmethod
    def size(self) -> ElaboratableValue:
        """All ``Logic`` subclasses should have an elaboratable size (the number of bits)"""


class Bit(Logic):
    """A single bit type. Equivalent to ``logic`` or ``logic[0:0]`` type in Verilog."""

    @property
    def size(self) -> ElaboratableValue:
        return ElaboratableValue(1)

    @override
    def copy(self):
        return Bit(name=self.name)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Bit):
            return True and super().__eq__(value)
        return NotImplemented


_ArrayItemOrField = TypeVar("_ArrayItemOrField", bound=Logic, covariant=True)


class LogicArray(Logic, Generic[_ArrayItemOrField]):
    """A type representing a multidimensional array of logical elements."""

    dimensions: list[Dimensions]
    item: _ArrayItemOrField

    @property
    def size(self):
        return self.item.size * reduce(
            lambda a, b: (b.upper - b.lower) * a, self.dimensions, ElaboratableValue(0)
        )

    @override
    def copy(self):
        return LogicArray(
            name=self.name, dimensions=(deepcopy(d) for d in self.dimensions), item=self.item.copy()
        )

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        dimensions: Iterable[Dimensions],
        item: _ArrayItemOrField,
    ):
        """
        Constructs the array type

        :param dimensions: An iterable of dimensions of the array.
            E.g. A ``logic[7:0][31:0]`` type has ``[(7:0), (31:0)]`` dimensions.
        """

        super().__init__(name)
        self.dimensions = list(dimensions)
        self.item = item
        set_parent(item, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, LogicArray):
            return (
                self.dimensions == value.dimensions
                and self.item == value.item
                and super().__eq__(value)
            )
        return NotImplemented


class Bits(LogicArray[Bit]):
    """A multidimensional array of bits"""

    def __init__(self, *, name: Optional[str] = None, dimensions: Iterable[Dimensions]):
        super().__init__(dimensions=dimensions, item=Bit(), name=name)


class Enum(Bits):
    """
    A bit vector limited to a range of predefined variants,
    each one with an explicit name.
    """

    variants: dict[str, ElaboratableValue]

    @override
    def copy(self):
        return Enum(
            name=self.name,
            dimensions=[deepcopy(d) for d in self.dimensions],
            variants=deepcopy(self.variants),
        )

    def __init__(
        self,
        *,
        name: Optional[VariableName] = None,
        dimensions: Collection[Dimensions] = (),
        variants: Mapping[str, ElaboratableValue],
    ):
        if len(dimensions) == 0:
            upper = max(v for v in variants.values()).elaborate() if len(variants) != 0 else 1
            assert upper is not None
            dimensions = [Dimensions(upper=ElaboratableValue(ceil(log2(upper))))]
        super().__init__(name=name, dimensions=dimensions)
        self.variants = dict(variants)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Enum):
            return super().__eq__(value) and self.variants == value.variants
        return NotImplemented


class StructField(Logic, Generic[_ArrayItemOrField]):
    """A field in a ``BitStruct``"""

    type: _ArrayItemOrField
    field_name: VariableName

    @override
    def copy(self):
        return StructField(name=self.field_name, type=self.type.copy())

    @property
    def size(self):
        return self.type.size

    def __init__(self, *, name: VariableName, type: _ArrayItemOrField) -> None:
        super().__init__()
        self.name = self.field_name = name
        self.type = type
        set_parent(type, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, StructField):
            return self.name == value.name and self.type == value.type and super().__eq__(value)
        return NotImplemented


class BitStruct(Logic):
    """A complex structural type equivalent to a ``struct {...}`` construct in SystemVerilog."""

    fields: list[StructField[Logic]]

    @override
    def copy(self):
        return BitStruct(name=self.name, fields=(f.copy() for f in self.fields))

    @property
    def size(self):
        return reduce(lambda a, b: a + b.type.size, self.fields, ElaboratableValue(0))

    def __init__(self, *, name: Optional[str] = None, fields: Iterable[StructField[Logic]]) -> None:
        super().__init__(name)
        self.fields = list(fields)
        for f in fields:
            set_parent(f, self)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, BitStruct):
            return self.fields == value.fields and super().__eq__(value)
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

    def overlaps(self, other: LogicSelect) -> bool:
        """
        Checks if this selection of a logic type overlaps with
        another selection. An overlap occurs if two selections
        of types flatten to a packed bit-vector would target a range
        of the same bits. E.g.:

            logic [127:0] a;
            wire [63:0] b = a[63:0];
            wire [63:0] c = a[127:64];
            wire [51:0] d = a[100:50];

            assert not b.overlaps(c) and not c.overlaps(b)
            assert b.overlaps(d)
            assert c.overlaps(d)
            assert d.overlaps(c) and d.overlaps(b)
        """

        if self.logic != other.logic:
            return False
        for op1, op2 in zip_longest(self.ops, other.ops):
            if op1 is None:
                op1 = op2
            if op2 is None:
                op2 = op1
            if isinstance(op1, LogicFieldSelect):
                if op1.field != cast(LogicFieldSelect, op2).field:
                    return False
            elif isinstance(op1, LogicBitSelect):
                op2 = cast(LogicBitSelect, op2)
                if op1.slice.upper <= op2.slice.lower or op1.slice.lower >= op2.slice.upper:
                    return False
        return True


@dataclass
class LogicFieldSelect:
    """Represents access operation to a field of a structure"""

    field: StructField[Logic]


@dataclass
class LogicBitSelect:
    """Represents a logic array indexing operation"""

    slice: Dimensions
