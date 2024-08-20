# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import itertools
import re
from dataclasses import field
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Sequence,
    TypeVar,
    Union,
)

import marshmallow
import marshmallow_dataclass


class RegexpField(marshmallow.fields.Field):
    """
    Marshmallow field representing a regexp.
    Checks for regex validity on deserialization.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        return value.pattern

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return re.compile(value)
        except Exception as e:
            raise marshmallow.ValidationError(f"Regexp {value} is invalid: {str(e)}")


RegexpT = marshmallow_dataclass.NewType("RegexpT", re.Pattern, field=RegexpField)


T = TypeVar("T")
U = TypeVar("U")
W = TypeVar("W")
NestedDict = Dict[T, Union[U, "NestedDict"]]
FlatTree = List[Sequence[T]]
AnnotatedFlatTree = Iterable[Dict[T, U]]


def flatten_tree(tree: NestedDict[T, U]) -> FlatTree[Union[T, U]]:
    """
    Flattens a nested dictionary by removing mappings key: value and transforming them to
    tuples (key, value) recursively, flattening the tuples in the process.

    Example:
    flatten_tree({
        "a": "foo",
        "b": {
            "bar": 1,
            "baz": 2,
            "foobar": [1, 2, 3]
        }
    }) == [
        ("a", "foo"),
        ("b", "bar", 1),
        ("b", "baz", 2),
        ("b", "foobar", [1, 2, 3]),
    ]
    """

    def flatten(t):
        for k, v in t.items():
            if isinstance(v, dict):
                for elem in flatten_tree(v):
                    yield (k, *elem)
            elif v is not None:
                yield (k, v)

    return list(flatten(tree))


def annotate_flat_tree(flat_tree: FlatTree[U], field_names: List[T]) -> AnnotatedFlatTree[T, U]:
    """
    Transforms a flattened tree (such as one returned by `flatten_tree`) into a list of dictionaries,
    with each dictionary mapping names from `field_names` to consecutive elements of a single item in `flat_tree`.
    All elements in `flat_tree` must have the same length and it must match the length of `field_names`.

    Example:
    annotate_flat_tree([
        ("in", "clk", 1),
        ("in", "data_in", 32),
        ("out", "data_out", 16),
    ], ["direction", "name", "width"]) == [
        {
            "direction": "in",
            "name": "clk",
            "width": 1,
        },
        {
            "direction": "in",
            "name": "data_in",
            "width": 32,
        },
        {
            "direction": "out",
            "name": "data_out",
            "width": 16,
        },
    ]
    """

    def mapfunc(elem: Sequence[T]) -> Dict[T, U]:
        # make sure that len(field_names) == len(elem)
        if len(field_names) > len(elem):
            raise ValueError(f"Missing nested fields named {field_names[len(elem):]}")
        elif len(field_names) < len(elem):
            raise ValueError(f"Too many levels of nested fields named {elem[len(field_names):]}")
        # pair each field with its name
        return dict(zip(field_names, elem))

    return list(map(mapfunc, flat_tree))


def unflatten_annotated_tree(
    flat_annot_tree: AnnotatedFlatTree[T, U], field_order: List[T], sort: bool = False
) -> NestedDict[U, U]:
    """
    Transforms a flat annotated tree `flat_annot_tree` (such as one returned by `annotate_flat_tree`) back into
    a nested dictionary grouped by values of fields in `flat_annot_tree` defined in `field_order`.

    Order of nesting (i.e. what fields should be higher in the hierarchy) is defined by order in `field_order` -
    elements appearing earlier will be higher in the nested dict hierarchy. All elements in `field_order` must
    be keys in all elements of `flat_annot_tree`. For all fields that occur in an element of `flat_annot_tree`
    to be included, all of them must be listed in `field_order`. If there are two elements in `flat_annot_tree`
    that have equal values of non-leaf keys, all leaf values are grouped into a list.

    Example:
    flat_annot_tree = [
        {
            "type": "required",
            "direction": "in",
            "name": "clk",
            "width": 1,
        },
        {
            "type": "required",
            "direction": "in",
            "name": "data_in",
            "width": 32,
        },
        {
            "type": "required",
            "direction": "out",
            "name": "data_out",
            "width": 16,
        },
        {
            "type": "optional",
            "direction": "out",
            "name": "valid",
            "width": 1,
        },
        {
            "type": "optional",
            "direction": "out",
            "name": "valid",
            "width": 15,
        }
    ]

    # all fields listed in `field_order`
    unflatten_annotated_tree(flat_annot_tree, ["type", "direction", "name", "width"]) == {
        "required": {
            "out": {
                "data_out": 16,
            },
            "in": {
                "clk": 1,
                "data_in": 32,
            },
        },
        "optional": {
            "out": {
                "valid": [1, 15],
            },
        },
    }

    # "direction" field skipped in `field_order`
    unflatten_annotated_tree(flat_annot_tree, ["type", "direction", "name"]) == {
        "required": {
            "clk": 1,
            "data_in": 32,
            "data_out": 16,
        },
        "optional": {
            "valid": [1, 15],
        },
    }
    """
    res = {}

    # we've reached leaf node
    if len(field_order) == 1:
        [leaf_field_name] = field_order
        if len(flat_annot_tree) == 1:
            # if there's only one element left, return it as-is
            [elem] = flat_annot_tree
            return elem[leaf_field_name]
        else:
            # if there are more, return a list of them
            return [elem[leaf_field_name] for elem in flat_annot_tree]

    def keyfunc(elem):
        return elem[field_order[0]]

    for key, g in itertools.groupby(
        sorted(flat_annot_tree, key=keyfunc) if sort else flat_annot_tree, key=keyfunc
    ):
        res[key] = unflatten_annotated_tree(list(g), field_order[1:])

    return res


def optional_with(
    default_factory: Callable[[], Any], meta_kw: Mapping[str, Any] = {}, **kwargs: Any
):
    """
    A shorthand specification for a marshmallow_dataclasses field to be optional and default initialized

    :param default_factory: A zero-argument callable to initialize the default value
    :param meta_kw: kwargs passed to marshmallow.Field
    :param **kwargs: Extra arguments passed to dataclass.field
    """

    return field(
        default_factory=default_factory,
        metadata={"load_default": default_factory, "required": False, **meta_kw},
        **kwargs,
    )


def flatten_and_annotate(
    data: NestedDict[T, U], field_names: List[W]
) -> AnnotatedFlatTree[W, Union[T, U]]:
    """
    A combination of annotate_flat_tree(flatten_tree(data)) possibly
    wrapped in marshmallow ValidationError commonly used in handlers
    """

    try:
        data = annotate_flat_tree(flatten_tree(data), field_names)
        return data
    except ValueError as e:
        raise marshmallow.ValidationError(str(e))
