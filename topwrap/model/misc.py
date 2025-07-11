# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import marshmallow
from typing_extensions import Self

if TYPE_CHECKING:
    from topwrap.model.module import Module


class TranslationError(Exception):
    """Fatal error while translating between IR and other formats"""


class RelationshipError(Exception):
    """Logic error of an IR hierarchy, like trying to double-assign a parent to an object"""


def set_parent(child: Any, parent: Any):
    if getattr(child, "parent", None) is not None:
        raise RelationshipError(f"{child} already has a parent reference")
    child.parent = parent


#: A placeholder for a future, possibly bounded type for IR object names.
#: For example we may want to reduce possible names to only alphanumerical
#: strings in the future.
VariableName = str

_E = TypeVar("_E")


class QuerableView(Sequence[_E]):
    """
    A lightweight proxy for exploring sequences of elements
    or concatenations of multiple sequences of elements
    in our IR, e.g. `Design.components`, `Module.ios`, etc.
    that has convenient methods for finding specific entries,
    for example by their name, which can replace such cumbersome constructs:

        comp = next((c for c in design.components if c.name == "name"), None)

    with:

        comp = design.components.find_by_name("name")
    """

    def __init__(self, *parts: Sequence[_E]) -> None:
        super().__init__()
        self._parts = parts

    def __contains__(self, x: object) -> bool:
        return any(x in part for part in self._parts)

    def __iter__(self) -> Iterator[_E]:
        return chain(*self._parts)

    def __len__(self) -> int:
        return sum(len(part) for part in self._parts)

    def __getitem__(self, key: int) -> _E:  # type: ignore # slicing is explicitly unsupported
        if key >= len(self) or key * -1 > len(self):
            raise IndexError
        acc = 0
        key = key if key >= 0 else len(self) + key
        for part in self._parts:
            acc += len(part)
            if key < acc:
                return part[key - acc + len(part)]

    def find_by(self, filter: Callable[[_E], bool]) -> Optional[_E]:
        for elem in self:
            if filter(elem):
                return elem

    def find_by_name(self, name: str) -> Optional[_E]:
        return self.find_by(lambda e: getattr(e, "name", None) == name)

    def find_by_name_or_error(self, name: str) -> _E:
        val = self.find_by_name(name)
        if val is None:
            raise ValueError(f"Could not find value named {name!r}")
        return val


class ModelBase(ABC):
    """
    This is a base class for all IR objects implementing common
    behavior that should be shared by all of them. Currently it
    only assigns them unique ``ObjectId`` s.
    """

    _id: ObjectId[Self]

    def __init__(self) -> None:
        self._id = ObjectId(self)


_T = TypeVar("_T", bound=ModelBase, covariant=True)


class ObjectId(Generic[_T]):
    """
    Represents a runtime-unique id for an IR object that can
    always be resolved to that object and can be used as a
    dictionary key/set value.
    """

    _last_id: ClassVar[int] = 0

    _id: int
    _objref: _T

    def __init__(self, obj: _T) -> None:
        id = self._last_id + 1
        self._id = ObjectId._last_id = id
        self._objref = obj

    def __hash__(self) -> int:
        return self._id

    def resolve(self) -> _T:
        """Resolve this id to a concrete object instance"""

        return self._objref


class ElaboratableValue:
    """
    A WIP class aiming to represent any generic value that can
    be resolved to a concrete constant during elaboration.

    It should be able to e.g. reference multiple ``Parameter`` s by name
    and perform arbitrary arithmetic operations on them.
    """

    value: str

    def __init__(self, expr: Union[int, str]) -> None:
        self.value = str(expr)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, ElaboratableValue):
            return self.value == value.value
        return NotImplemented

    def __add__(self, value: object) -> ElaboratableValue:
        if isinstance(value, ElaboratableValue):
            return ElaboratableValue(f"({self.value} + {value.value})")
        return NotImplemented

    def __sub__(self, value: object) -> ElaboratableValue:
        if isinstance(value, ElaboratableValue):
            return ElaboratableValue(f"({self.value} - {value.value})")
        return NotImplemented

    def __mul__(self, value: object) -> ElaboratableValue:
        if isinstance(value, ElaboratableValue):
            return ElaboratableValue(f"({self.value} * {value.value})")
        return NotImplemented

    def __str__(self) -> str:
        return self.value

    class DataclassRepr(marshmallow.fields.Field):
        def _serialize(
            self, value: ElaboratableValue, attr: str | None, obj: Any, **kwargs: Any
        ) -> Any:
            return value.value

        def _deserialize(
            self, value: Any, attr: str | None, data: Mapping[str, Any] | None, **kwargs: Any
        ) -> Any:
            return ElaboratableValue(value)

    Field = Annotated["ElaboratableValue", DataclassRepr]


@dataclass(frozen=True)
class Identifier:
    """
    An advanced identifier of some IR objects that
    can benefit from storing more information than
    just their name. Based on the VLNV convention.
    """

    name: str
    vendor: str = field(default="vendor")
    library: str = field(default="libdefault")

    def combined(self) -> str:
        return "_".join([self.vendor, self.library, self.name])


@dataclass
class FileReference:
    """A reference to a particular location in a text file on the filesystem"""

    file: Path
    line: int = field(default=0)
    column: int = field(default=0)


class Parameter(ModelBase):
    """Represents a parameter definition for a HDL module"""

    parent: Module
    name: VariableName

    #: If a value for this parameter was not provided
    #: during elaboration, this default will be used.
    default_value: Optional[ElaboratableValue]

    def __init__(
        self, *, name: VariableName, default_value: Optional[ElaboratableValue] = None
    ) -> None:
        super().__init__()
        self.name = name
        self.default_value = default_value

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Parameter):
            return self.name == value.name and self.default_value == value.default_value
        return NotImplemented
