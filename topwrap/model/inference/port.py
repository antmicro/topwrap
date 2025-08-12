# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from enum import Enum
from typing import (
    Annotated,
    Any,
    Iterator,
    Mapping,
    Optional,
    Union,
)

import marshmallow

from topwrap.model.connections import ReferencedPort
from topwrap.model.hdl_types import (
    BitStruct,
    Dimensions,
    LogicArray,
    LogicBitSelect,
    LogicFieldSelect,
    LogicSelect,
)
from topwrap.model.interface import InterfaceMode, InterfaceSignal
from topwrap.model.misc import ElaboratableValue
from topwrap.model.module import Module


class PortSelectorField(marshmallow.fields.Field):
    def _serialize(self, value: PortSelector, attr: Optional[str], obj: Any, **kwargs: Any) -> str:
        return str(value)

    def _deserialize(
        self, value: str, attr: Optional[str], data: Optional[Mapping[str, Any]], **kwargs: Any
    ) -> PortSelector:
        try:
            return PortSelector.from_str(value)
        except ValueError as e:
            raise marshmallow.ValidationError(f"Malformed port selector: {str(e)}") from e


class PortSelectorOp(Enum):
    FIELD = 1
    SLICE = 2


PortSelectorOpT = Union[
    tuple[PortSelectorOp.FIELD, str], tuple[PortSelectorOp.SLICE, tuple[int, int]]
]


SELECTOR_SLICE_REGEXP = re.compile(r"^\[\s*(?:(?:(\d+)\s*:\s*(\d+))|(\d+))\s*\]$")


@dataclass(frozen=True)
class PortSelector:
    """
    A selector of (potentially a smaller part of) a port.

    The selector starts with an external port name, and is followed by one or more of the
    following operations:

    * field selection (e.g. :code:`.some_field`),
    * array indexing/slicing (e.g. :code:`[1]` or :code:`[3:0]`).

    For example, accessing a part one of the manager port fields of an instance of :code:`axi_demux`
    from `pulp-platform/axi <https://github.com/pulp-platform/axi/>`_  would look like this:
    :code:`mst_reqs_o[2].ar.addr[3:0]`.
    """

    #: Name of the module port this selector targets.
    port: str

    #: Tuple of operations to be performed on the port.
    ops: tuple[PortSelectorOpT, ...]

    @classmethod
    def from_str(cls, sel: str) -> PortSelector:
        """
        Parse a port selector string into an instance of :class:`PortSelector`.
        """

        if not sel:
            raise ValueError("Empty port selector")

        def _parse_slices(part: str) -> Iterator[str]:
            for n, slice in enumerate(part.split("[")):
                if n == 0:
                    yield slice
                else:
                    if not slice.strip():
                        raise ValueError("Invalid bounds syntax")
                    yield "[" + slice

        parts = sel.split(".")
        parts = list(itertools.chain.from_iterable(_parse_slices(x) for x in parts))

        port = parts[0].strip()
        ops = list[PortSelectorOpT]()

        if not port:
            raise ValueError("Empty module port name")

        for part in parts[1:]:
            part = part.strip()
            if part and part[-1] == "]":
                match = SELECTOR_SLICE_REGEXP.fullmatch(part)
                if not match:
                    raise ValueError(f"Invalid bounds syntax '{part}'")

                # `hi` and `lo` are set for `[1:0]`, `idx` is set for `[0]`
                hi, lo, idx = match.groups()
                if idx:
                    idx = int(idx)
                    ops.append((PortSelectorOp.SLICE, (idx, idx)))
                else:
                    if not hi or not lo:
                        raise RuntimeError("Unexpected unmatched high/low part")
                    hi, lo = int(hi), int(lo)
                    ops.append((PortSelectorOp.SLICE, (hi, lo)))
            else:
                name = part.strip()
                if not name:
                    raise ValueError("Empty field name")
                ops.append((PortSelectorOp.FIELD, name))

        return PortSelector(port, tuple(ops))

    def __str__(self) -> str:
        """
        Represent a :class:`PortSelector` as a port selector string.
        """

        result = self.port

        for kind, params in self.ops:
            if kind == PortSelectorOp.FIELD:
                result = f"{result}.{params}"
            elif kind == PortSelectorOp.SLICE:
                (upper, lower) = params
                if upper == lower:
                    result = f"{result}[{upper}]"
                else:
                    result = f"{result}[{upper}:{lower}]"
            else:
                raise RuntimeError(f"Invalid operation kind '{kind}' in port selector")

        return result

    def make_referenced_port(
        self, module: Module, mode: InterfaceMode, signal: InterfaceSignal
    ) -> ReferencedPort:
        """
        Construct a :class:`ReferencedPort`, potentially with an instance of :class:`LogicSelect`
        based on the information contained in this selector.
        """

        port = module.ports.find_by_name(self.port)
        if not port:
            raise ValueError(f"Port specification references non-existent port {self.port}")

        if port.direction != signal.modes[mode].direction:
            raise ValueError(
                f"Referenced module port '{self.port}' has wrong direction ({port.direction} != "
                f"{signal.modes[mode].direction})"
            )

        ops = []
        cur = port.type
        for kind, params in self.ops:
            if kind == PortSelectorOp.FIELD:
                if not isinstance(cur, BitStruct):
                    raise ValueError(
                        f"Attempted to select field '{params}' in type something that is not a "
                        f"struct (type {cur.name})"
                    )

                fields = {x.field_name: x for x in cur.fields}
                if params not in fields:
                    raise ValueError(f"Field '{params}' is not a member of struct '{cur.name}'")

                field = fields[params]
                ops.append(LogicFieldSelect(field))
                cur = field.type
            elif kind == PortSelectorOp.SLICE:
                if not isinstance(cur, LogicArray):
                    raise ValueError(
                        f"Attempted to slice into something that is not an array (type {cur.name})"
                    )

                upper = ElaboratableValue(params[0])
                lower = ElaboratableValue(params[1])

                ops.append(LogicBitSelect(Dimensions(upper=upper, lower=lower)))

                # If we sliced through all dimensions of the array type, we can move on to accessing
                # the inner type.
                if all(isinstance(x, LogicBitSelect) for x in ops[-len(cur.dimensions) :]):
                    cur = cur.item
            else:
                raise RuntimeError(f"Invalid operation kind '{kind}' in port selector")

        return ReferencedPort.external(port, LogicSelect(port.type, ops) if ops else None)


PortSelectorT = Annotated[PortSelector, PortSelectorField]
