# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import logging
import math
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from functools import reduce
from itertools import zip_longest
from math import ceil, log2
from operator import mul
from typing import (
    TYPE_CHECKING,
    Collection,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    TypeVar,
    Union,
    cast,
)

import simpleeval
from typing_extensions import override

from topwrap.model.misc import (
    ElaboratableValue,
    ModelBase,
    ObjectId,
    Parameter,
    VariableName,
    set_parent,
)

if TYPE_CHECKING:
    from topwrap.model.interface import Interface, InterfaceDefinition, InterfaceSignal
    from topwrap.model.module import Module

logger = logging.getLogger(__name__)
_SYMBOLIC_DIM_RE = re.compile(r"[A-Za-z_$]")


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


def has_symbolic_dimensions(net_type: Optional[Logic]) -> bool:
    if net_type is None:
        return False
    dims = getattr(net_type, "dimensions", None) or []
    for dim in dims:
        upper = getattr(dim, "upper", None)
        lower = getattr(dim, "lower", None)
        if upper is not None and _SYMBOLIC_DIM_RE.search(str(upper)):
            return True
        if lower is not None and _SYMBOLIC_DIM_RE.search(str(lower)):
            return True
    return False


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
        item_val = self.item.size.elaborate()
        dim_vals = []
        for d in self.dimensions:
            up, low = d.upper.elaborate(), d.lower.elaborate()
            dim_vals.append(None if up is None or low is None else up - low + 1)

        if item_val is not None and all(v is not None for v in dim_vals):
            return ElaboratableValue(reduce(mul, dim_vals, item_val))

        one = ElaboratableValue(1)
        return reduce(
            lambda total, d: total * (d.upper - d.lower + one), self.dimensions, self.item.size
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
                (
                    len(self.dimensions) == len(value.dimensions)
                    and all(
                        [a == b for a, b in zip(self.dimensions, value.dimensions, strict=True)]
                    )
                )
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


class ElabvalueEvaluator:
    # This prefix is used to replace the $ char in SystemVerilog system functions
    # Simpleeval cannot parse $ and pure `clog2` could cause naming collisions
    sv_sysfunc_pfx = "_9263cec0fd53ad433112bdf3883bbd7216015109_"

    # More math functions can be added according to needs
    funcs = {
        sv_sysfunc_pfx + "clog2": lambda val: math.ceil(log2(val)),
    }

    @staticmethod
    def _sanitize(string: str) -> str:
        def convert_constants(string: str, lst: list[str], base: int):
            for match in lst:
                val = match.split("'", 1)
                val = val[1][1:]
                string = string.replace(match, str(int(val, base)))

            return string

        # remove '$' from input string, to allow eval to recognise functions properly
        # replace this with our prefix
        string = re.sub(r"\$", ElabvalueEvaluator.sv_sysfunc_pfx, string)

        # detect and replace verilog style value (e.g. 8'b11010011)
        # this should also match something like width'd12 and 'o7
        matches_bin = re.findall(r"(?<!\w)(?:[a-zA-Z_]\w*|[0-9]+)?\'b[0-1]+\b", string)
        matches_dec = re.findall(r"(?<!\w)(?:[a-zA-Z_]\w*|[0-9]+)?\'d[0-9]+\b", string)
        matches_oct = re.findall(r"(?<!\w)(?:[a-zA-Z_]\w*|[0-9]+)?\'o[0-7]+\b", string)
        matches_hex = re.findall(r"(?<!\w)(?:[a-zA-Z_]\w*|[0-9]+)?\'h[0-9a-fA-F]+\b", string)

        string = re.sub(r"(?<!\w)'0\b", "0", string)
        matches_1 = re.findall(r"(?<!\w)'1\b", string)
        if len(matches_1) > 1:
            logger.warning("'1 detected in parameter value; it cannot be handled!")

        string = convert_constants(string, matches_bin, 2)
        string = convert_constants(string, matches_oct, 8)
        string = convert_constants(string, matches_dec, 10)
        string = convert_constants(string, matches_hex, 16)

        return string

    @staticmethod
    # TODO This function has an edge case when
    # parameter in intfdefinition and module has the same name!
    def substitute_intf_params_for_module(
        intf: InterfaceDefinition, mod: Module, params: dict[ObjectId[Parameter], ElaboratableValue]
    ) -> dict[ObjectId[InterfaceSignal], Logic]:
        combined = {}
        for parameter in intf.parameters:
            if params.get(parameter._id, None) is None:
                combined[parameter._id] = parameter.default_value
            else:
                combined[parameter._id] = params[parameter._id]

        res = {}
        for sig in intf.signals:
            if isinstance(sig.type, Bit):
                res[sig._id] = Bit()
            elif isinstance(sig.type, Bits):
                upp = sig.type.dimensions[0].upper.value
                low = sig.type.dimensions[0].lower.value

                for param, val in combined.items():
                    upp = re.sub(rf"\b{re.escape(param.resolve().name)}\b", f"({val.value})", upp)
                    low = re.sub(rf"\b{re.escape(param.resolve().name)}\b", f"({val.value})", low)

                upp = ElaboratableValue(upp)
                low = ElaboratableValue(low)
                res[sig._id] = Bits(dimensions=[Dimensions(upper=upp, lower=low)])

        return res

    @staticmethod
    def resolve_intf_values(
        intf: Interface,
        instance: dict[ObjectId[Parameter], ElaboratableValue],
    ) -> tuple[
        Mapping[ObjectId[Parameter], ElaboratableValue], Mapping[ObjectId[InterfaceSignal], Logic]
    ]:
        """
        Resolve interface parameters to their integer values and
        Resolve interface signals types to their final types
        """
        inst_combined, inst_env = ElabvalueEvaluator._preprocess_params(
            instance, intf.parent.parameters
        )
        inst_params = ElabvalueEvaluator._resolve_params(inst_combined, inst_env)

        intf_params = dict[ObjectId[Parameter], ElaboratableValue]()
        for k, v in intf.parameters.items():
            try:
                val = ElabvalueEvaluator._sanitize(v.value)
                intf_params[k] = ElaboratableValue(
                    int(
                        simpleeval.simple_eval(
                            val, names=inst_params, functions=ElabvalueEvaluator.funcs
                        )
                    )
                )
            except (simpleeval.InvalidExpression, SyntaxError) as e:
                logger.warning(
                    f"cannot resolve parameter {k.resolve().name} from intf {intf.name} due to {e}"
                )
                intf_params[k] = v

        intf_combined, intf_env = ElabvalueEvaluator._preprocess_params(
            intf_params, intf.definition.parameters
        )
        intf_params_resolved = ElabvalueEvaluator._resolve_params(intf_combined, intf_env)

        sigtypes = {}
        for sig in intf.signals:
            sigtypes[sig] = ElabvalueEvaluator._eval_type(sig.resolve().type, intf_params_resolved)
        paramvals = dict[ObjectId[Parameter], ElaboratableValue]()
        for param in intf.parameters.keys():
            paramvals[param] = ElaboratableValue(intf_params_resolved[param.resolve().name])

        return paramvals, sigtypes

    @staticmethod
    def _preprocess_params(
        map: dict[ObjectId[Parameter], ElaboratableValue],
        defaults: Iterable[Parameter],
    ) -> tuple[dict[str, str], dict[str, int]]:
        # Combine map and defaults into single dict
        combined = dict[str, str]()
        for param, val in map.items():
            param = param.resolve()
            combined[param.name] = val.value

        for param in defaults:
            if combined.get(param.name) is None:
                if param.default_value is None:
                    logger.warning(f"parameter '{param.name}' has no default or assigned value")
                    continue
                combined[param.name] = param.default_value.value

        for param in combined:
            combined[param] = ElabvalueEvaluator._sanitize(combined[param])

        # resolve all parameters to their values and put them in env
        env = dict[str, int]()
        for param, pval in combined.items():
            for other, oth_val in combined.items():
                if param == other:
                    continue
                combined[other] = re.sub(rf"\b{re.escape(param)}\b", f"({pval})", oth_val)

        for p, v in combined.items():
            deps = list(ElabvalueEvaluator.get_elab_value_deps((ElaboratableValue(v)), defaults))
            if len(deps) == 0:
                try:
                    env[p] = int(
                        simpleeval.simple_eval(v, names=env, functions=ElabvalueEvaluator.funcs)
                    )
                except (simpleeval.InvalidExpression, SyntaxError) as e:
                    logger.warning(
                        f"cannot evaluate independent expression for parameter {p}: {v} due to {e}"
                    )

        return combined, env

    @staticmethod
    def just_eval(val: ElaboratableValue, env: dict[str, int]) -> int:
        return int(simpleeval.simple_eval(val.value, names=env, functions=ElabvalueEvaluator.funcs))

    @staticmethod
    def _resolve_params(combined: dict[str, str], env: dict[str, int]) -> dict[str, int]:
        params = env.copy()
        for param, val in combined.items():
            try:
                res = int(
                    simpleeval.simple_eval(val, names=env, functions=ElabvalueEvaluator.funcs)
                )
                params[param] = res
            except (simpleeval.InvalidExpression, SyntaxError):
                pass
                # Some params are not used for width definitions and will never eval to any value
                # They can be skipped, and evaluation may still succeed
        return params

    @staticmethod
    def _eval_type(type: Logic, env: dict[str, int]) -> Logic:
        if isinstance(type, Bit):
            return type
        elif isinstance(type, LogicArray):
            result = type.copy()
            for i in range(len(result.dimensions)):
                dims = result.dimensions[i]

                res = ElabvalueEvaluator._eval_dims(dims, env)
                result.dimensions[i] = res

            return result

        # currently only Logic Array is supported
        return type

    @staticmethod
    def _eval_dims(dims: Dimensions, env: dict[str, int]) -> Dimensions:
        upp = ElabvalueEvaluator._sanitize(dims.upper.value)
        lwr = ElabvalueEvaluator._sanitize(dims.lower.value)

        try:
            uval = int(simpleeval.simple_eval(upp, names=env, functions=ElabvalueEvaluator.funcs))
            lval = int(simpleeval.simple_eval(lwr, names=env, functions=ElabvalueEvaluator.funcs))
        except (simpleeval.InvalidExpression, SyntaxError) as e:
            logger.warning(f"Cannot infer port widths; {e}")
            return dims

        return Dimensions(upper=ElaboratableValue(uval), lower=ElaboratableValue(lval))

    @staticmethod
    def get_elab_value_deps(
        val: ElaboratableValue, params: Iterable[Parameter]
    ) -> Iterator[Parameter]:
        """
        For a given ElaboratableValue and a set of parameters find out which parameters it uses
        """

        used_names = set[str]()

        def handler(node: ast.Name):
            if node.id not in ElabvalueEvaluator.funcs:
                used_names.add(node.id)
            return 1

        try:
            simpleeval.simple_eval(
                ElabvalueEvaluator._sanitize(val.value),
                names=handler,
                functions=ElabvalueEvaluator.funcs,
            )
        except (simpleeval.InvalidExpression, SyntaxError) as e:
            logger.warning(f"failure during elabvalue dependency check; {e}")
            return

        yield from (p for p in params if p.name in used_names)
