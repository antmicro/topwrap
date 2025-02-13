# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Generic,
    Mapping,
    Optional,
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
    setattr(child, "parent", parent)


#: A placeholder for a future, possibly bounded type for IR object names.
#: For example we may want to reduce possible names to only alphanumerical
#: strings in the future.
VariableName = str


class ModelBase(ABC):
    """
    This is a base class for all IR objects implementing common
    behavior that should be shared by all of them. Currently it
    only assigns them unique ``ObjectId`` s.
    """

    _id: ObjectId[Self]

    def __init__(self) -> None:
        self._id = ObjectId(self)


_T = TypeVar("_T", bound=ModelBase)


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

    # This should be specific to the KPM layer, but it would be
    # really difficult to do it in such a way. If we ever implement
    # an IR-literal layer that can serialize and deserialize the
    # entire IR, this as well as `topwrap.backend.kpm.common.InterconnectParamSerializer`
    # could probably be heavily simplified and generalized.
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


@dataclass
class Identifier(ModelBase):
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
    line: int
    column: int


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
