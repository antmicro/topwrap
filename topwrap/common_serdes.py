# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Pattern,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

import marshmallow
import yaml
from typing_extensions import Annotated, Self

from topwrap.resource_field import (
    PathContext,
    ResourceReferenceHandler,
    YamlCommonSchemes,
)
from topwrap.util import MISSING, MaybeMissing


class RegexpField(marshmallow.fields.Field):
    """
    Marshmallow field representing a regexp.
    Checks for regex validity on deserialization.
    """

    def _serialize(self, value: Any, attr: Optional[str], obj: Any, **kwargs: Any):
        return value.pattern

    def _deserialize(
        self, value: Any, attr: Optional[str], data: Optional[Mapping[str, Any]], **kwargs: Any
    ):
        try:
            return re.compile(value)
        except Exception as e:
            raise marshmallow.ValidationError(f"Regexp {value} is invalid: {str(e)}")


class ResourcePathField(marshmallow.fields.Field):
    """
    Marshmallow field supporting resource reference
    strings as defined in `resource_field.py` using
    the `YamlCommonSchemes` supported schemes group
    """

    def _serialize(self, value: Any, attr: Optional[str], obj: Any, **kwargs: Any):
        if not isinstance(value, ResourceReferenceHandler):
            raise marshmallow.ValidationError(f"Invalid type: '{type(value)}'")
        value.update_meta(self.context)
        return value.to_str()

    def _deserialize(
        self, value: Any, attr: Optional[str], data: Optional[Mapping[str, Any]], **kwargs: Any
    ):
        if not isinstance(value, str):
            raise marshmallow.ValidationError(f"Invalid type: '{type(value)}'")
        ident = YamlCommonSchemes.parse(value)
        ident.update_meta(self.context)
        return ident


RegexpT = Annotated[Pattern[str], RegexpField]
ResourcePathT = Annotated[ResourceReferenceHandler, ResourcePathField]


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


class MetaKeys(Enum):
    SELF_CLEANUP = "self_cleanup"
    DEEP_CLEANUP = "deep_cleanup"
    INLINE_DEPTH = "inline_depth"

    SHOULD_INLINE = "should_inline"


def ext_field(
    default: MaybeMissing[Union[T, Callable[[], T]]] = MISSING,
    *,
    self_cleanup: bool = True,
    deep_cleanup: bool = False,
    inline_depth: Optional[int] = None,
    dcls_field_kws: Mapping[str, Any] = {},
    **kwargs: Any,
) -> T:
    """
    A shorthand wrapper for a marshmallow_dataclass field.
    Useful for specifying a field that should be optional and have a default value
    or a field that uses topwrap's extended functionality such as `deep_cleanup` without being very verbose.

    **For topwrap's extended functionality params (`self_cleanup`, `deep_cleanup`) to be useful, the target
    dataclass needs to inherit from `MarshmallowDataclassExtensions`, otherwise using them is a no-op.**

    Examples:
    - Specifying optional fields with default values::

        int_field: int = ext_field(42)
        list_field: List[str] = ext_field(list)
        filled_list: List[int] = ext_field(lambda: [1,2])

    - Passing additional [parameters to the `marshmallow.Field` class](https://marshmallow.readthedocs.io/en/stable/marshmallow.fields.html#marshmallow.fields.Field)
      is done through additional kwargs::

        field: str = ext_field(validate=validator_func)
        source: str = ext_field("/tmp", data_key="from") # you can combine that with the default value!

    - Passing additional [parameters to the `dataclass.field` function](https://docs.python.org/3/library/dataclasses.html#dataclasses.field)
      is done through the `dcls_field_kws` parameter::

        field: int = ext_field(dcls_field_kws={"repr": False})

    - Topwrap's extended field functionality is controlled through keyword parameters explicitly
      defined in the signature of this function::

        field: Dict[str, int] = ext_field(dict, deep_cleanup=True, self_cleanup=False)

    :param default: Either a zero-argument callable that initializes and returns a default value
        for this field or a plain default value. The presence of this parameter defines whether this
        field is optional in the generated schema or not.

    :param self_cleanup: If this field is optional, and this parameter is True then this field gets
        removed from the serialized data if it only contains a falsy value, ex. an empty dict or an
        empty list. *Setting this to True on a required field is a no-op.*

    :param deep_cleanup: If this field is a dict or a list and this parameter is True then during
        serialization this field would get recursively cleaned up of empty inner items. *Setting
        this to True on a field with type other than the above is a no-op.*

    :param inline_depth: Nested fields starting from this depth will be represented in an inline
        style (in other words, the "flow" style in YAML terminology).

    :param dcls_field_kws: Additional keyword params to be passed to the `dataclasses.field` function.

    :param **kwargs: Additional keyword params that get passed to the `marshmallow.Field` constructor.
    """

    if "metadata" not in kwargs:
        kwargs["metadata"] = {}
    kwargs["metadata"][MetaKeys.SELF_CLEANUP.value] = self_cleanup
    kwargs["metadata"][MetaKeys.DEEP_CLEANUP.value] = deep_cleanup
    kwargs["metadata"][MetaKeys.INLINE_DEPTH.value] = inline_depth

    if default is MISSING:
        return field(metadata=kwargs, **dcls_field_kws)

    opt_dcls_meta = {"load_default": default, "required": False, **kwargs}

    if isinstance(default, Callable):
        return field(default_factory=default, metadata=opt_dcls_meta, **dcls_field_kws)

    return field(default=default, metadata=opt_dcls_meta, **dcls_field_kws)


@dataclass
class Inline(Generic[T]):
    inner: T


class InlineYamlDumper(yaml.SafeDumper):
    """
    A custom YAML dumper that represents data wrapped with the `Inline`
    wrapper using the inline "flow style".
    """

    @staticmethod
    def represent_inline(dumper: yaml.SafeDumper, data: Inline[T]) -> yaml.Node:
        node = dumper.represent_data(data.inner)
        if isinstance(node, yaml.CollectionNode):
            node.flow_style = True
        return node


InlineYamlDumper.add_representer(Inline, InlineYamlDumper.represent_inline)


class MarshmallowDataclassExtensions:
    """
    This base class implements some common methods often used throughout the codebase
    and handles the usage of extended functionality parameters defined in the `ext_field(...)`
    function. The correct usage is to inherit from this class in your dataclass.
    """

    Schema: ClassVar[Type[marshmallow.Schema]]

    @staticmethod
    @marshmallow.post_dump(pass_original=True)
    def _post_dump_handler(
        sch: marshmallow.Schema,
        data: Dict[str, Any],
        org: MarshmallowDataclassExtensions,
        **kw: Any,
    ):
        data = org._cleanup_nulls(data, sch)
        if sch.context.get(MetaKeys.SHOULD_INLINE.value, False):
            data = org._inline_wrap(data, sch)
        return data

    @staticmethod
    def _cleanup_nulls(data: Dict[str, Any], sch: marshmallow.Schema) -> Any:
        """
        Walks through a serialized object and its corresponding marshmallow
        schema in order to remove any entries containing falsy, not required values.
        """

        def _test_null(obj: Any) -> bool:
            """
            Tests if this object should be removed. It should be removed when it
            evaluates to false and is an instance of one of these specific container types
            """
            return not obj and isinstance(obj, (dict, list, set, tuple, type(None)))

        def _deep_del(obj: Any, key: Union[str, int]):
            if isinstance(obj[key], dict):
                for next_key in obj[key]:
                    _deep_del(obj[key], next_key)
                obj[key] = {k: v for k, v in obj[key].items() if not _test_null(v)}
            elif isinstance(obj[key], (list, tuple)):
                for idx in range(len(obj[key])):
                    _deep_del(obj[key], idx)
                obj[key] = type(obj[key])(x for x in obj[key] if not _test_null(x))

        for fname, fld in sch.fields.items():
            name = fld.data_key or fname
            if fld.metadata.get(MetaKeys.DEEP_CLEANUP.value, False) and isinstance(
                fld, (marshmallow.fields.Dict, marshmallow.fields.List)
            ):
                _deep_del(data, name)
            if (
                not fld.required
                and fld.metadata.get(MetaKeys.SELF_CLEANUP.value, False)
                and _test_null(data[name])
            ):
                del data[name]

        return data

    @classmethod
    def _inline_wrap(cls, data: Dict[str, Any], sch: marshmallow.Schema) -> Any:
        """Wraps fields pointed by the `inlined` field parameter with the `Inline`
        wrapper which later gets caught by a custom PyYAML representer"""

        def _wrap_at_depth(data: Any, key: Any, depth: int):
            if depth <= 0:
                data[key] = Inline(data[key])
            else:
                if isinstance(data[key], (Mapping, list, tuple)):
                    keys = (
                        data[key].keys()
                        if isinstance(data[key], Mapping)
                        else range(len(data[key]))
                    )
                    for next_key in keys:
                        _wrap_at_depth(data[key], next_key, depth - 1)

        for fname, fld in sch.fields.items():
            name = fld.data_key or fname
            if (
                name in data
                and (depth := fld.metadata.get(MetaKeys.INLINE_DEPTH.value)) is not None
            ):
                _wrap_at_depth(data, name, depth)
        return data

    def to_dict(self, **kwargs: Any) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.Schema().dump(self, **kwargs))

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs: Any) -> Self:
        return cast(Self, cls.Schema().load(data, **kwargs))

    def to_yaml(self, **kwargs: Any) -> str:
        sch = self.Schema()
        sch.context[MetaKeys.SHOULD_INLINE.value] = True
        return yaml.dump(sch.dump(self), Dumper=InlineYamlDumper, sort_keys=True, **kwargs)

    @classmethod
    def from_yaml(cls, yaml_str: str, **kwargs: Any) -> Self:
        return cls.from_dict(yaml.safe_load(yaml_str, **kwargs))

    def save(self, path: Path, **kwargs: Any):
        with open(path, "w") as f:
            sch = self.Schema()
            sch.context[PathContext.CONTEXT_SAVE.value] = path
            f.write(yaml.safe_dump(sch.dump(self), sort_keys=True, **kwargs))

    @classmethod
    def load(cls, path: Path, **kwargs: Any) -> Self:
        with open(path) as f:
            sch = cls.Schema()
            sch.context[PathContext.CONTEXT_LOAD.value] = path
            return cast(Self, sch.load(yaml.safe_load(f, **kwargs)))
