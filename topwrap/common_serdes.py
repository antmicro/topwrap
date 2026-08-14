# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from textwrap import indent
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Mapping,
    Optional,
    Pattern,
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
            raise marshmallow.ValidationError(f"Regexp {value} is invalid: {str(e)}") from e


class ResourcePathField(marshmallow.fields.Field):
    """
    Marshmallow field supporting resource reference
    strings as defined in `resource_field.py` using
    the `YamlCommonSchemes` supported schemes group
    """

    def _serialize(self, value: Any, attr: Optional[str], obj: Any, **kwargs: Any):
        if value is None:
            # an Optional[ResourcePathT] that was left unset
            return None
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


_DICTKEY = TypeVar("_DICTKEY")
_DICTVAL = TypeVar("_DICTVAL")


class MetaKeys(Enum):
    SELF_CLEANUP = "self_cleanup"
    DEEP_CLEANUP = "deep_cleanup"
    INLINE_DEPTH = "inline_depth"

    SHOULD_INLINE = "should_inline"


def ext_field(
    default: MaybeMissing[Union[_DICTKEY, Callable[[], _DICTVAL]]] = MISSING,
    *,
    self_cleanup: bool = True,
    deep_cleanup: bool = False,
    inline_depth: Optional[int] = None,
    dcls_field_kws: Mapping[str, Any] = {},
    **kwargs: Any,
) -> _DICTKEY:
    """
    A shorthand wrapper for a marshmallow_dataclass field.
    Useful for specifying a field that should be optional and have a default value
    or a field that uses topwrap's extended functionality such as `deep_cleanup` without being very
    verbose.

    **For topwrap's extended functionality params (`self_cleanup`, `deep_cleanup`) to be useful, the
    target dataclass needs to inherit from `MarshmallowDataclassExtensions`, otherwise using them is
    a no-op.**

    Examples:
    - Specifying optional fields with default values::

        int_field: int = ext_field(42)
        list_field: List[str] = ext_field(list)
        filled_list: List[int] = ext_field(lambda: [1,2])

    - Passing additional [parameters to the `marshmallow.Field` class](https://marshmallow.readthedocs.io/en/stable/marshmallow.fields.html#marshmallow.fields.Field)
      is done through additional kwargs::

        field: str = ext_field(validate=validator_func)
        source: str = ext_field("/tmp", data_key="from") # you can combine that with the default
                                                         # value!

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

    :param dcls_field_kws: Additional keyword params to be passed to the `dataclasses.field`
        function.

    :param **kwargs: Additional keyword params that get passed to the `marshmallow.Field`
        constructor.
    """

    if "metadata" not in kwargs:
        kwargs["metadata"] = {}
    kwargs["metadata"][MetaKeys.SELF_CLEANUP.value] = self_cleanup
    kwargs["metadata"][MetaKeys.DEEP_CLEANUP.value] = deep_cleanup
    kwargs["metadata"][MetaKeys.INLINE_DEPTH.value] = inline_depth

    if "marshmallow_field" in kwargs:
        kwargs["marshmallow_field"].metadata.update(kwargs["metadata"])

    if default is MISSING:
        return field(metadata=kwargs, **dcls_field_kws)

    opt_dcls_meta = {"load_default": default, "required": False, **kwargs}

    if isinstance(default, Callable):
        return field(default_factory=default, metadata=opt_dcls_meta, **dcls_field_kws)

    return field(default=default, metadata=opt_dcls_meta, **dcls_field_kws)


@dataclass
class Inline(Generic[_DICTKEY]):
    inner: _DICTKEY


class InlineYamlDumper(yaml.SafeDumper):
    """
    A custom YAML dumper that represents data wrapped with the `Inline`
    wrapper using the inline "flow style".
    """

    @staticmethod
    def represent_inline(dumper: yaml.SafeDumper, data: Inline[_DICTKEY]) -> yaml.Node:
        node = dumper.represent_data(data.inner)
        if isinstance(node, yaml.CollectionNode):
            node.flow_style = True
        return node

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        """Override the increase_indent to never be indentless; this affects mostly lists,
        which we want to be indented"""
        return super().increase_indent(flow, False)

    @staticmethod
    def format_bool(dumper: yaml.SafeDumper, data: bool):
        return dumper.represent_scalar("tag:yaml.org,2002:bool", "True" if data else "False")


InlineYamlDumper.add_representer(Inline, InlineYamlDumper.represent_inline)
InlineYamlDumper.add_representer(bool, InlineYamlDumper.format_bool)


class HexInt(int):
    pass


class HexIntField(marshmallow.fields.Integer):
    def _serialize(self, value: int, attr: Optional[str], obj: Any, **kwargs: Any):
        return HexInt(value)

    def _deserialize(
        self, value: Any, attr: Optional[str], data: Optional[Mapping[str, Any]], **kwargs: Any
    ):
        super_val = super()._deserialize(value, attr, data, **kwargs)
        if super_val or super_val == 0:
            return HexInt(super_val)
        raise ValueError("Expecting value convertible to integer")


def represent_hex_int(dumper: InlineYamlDumper, data: HexInt) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:int", hex(data))


InlineYamlDumper.add_representer(HexInt, represent_hex_int)


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
            if name not in data:
                continue
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

    def to_yaml(self, pretty_format: bool = False, **kwargs: Any) -> str:
        sch = self.Schema()
        sch.context[MetaKeys.SHOULD_INLINE.value] = True

        def _dump_design(des: Any, is_toplevel: bool = True):
            """Dump a design to YAML in string. This has to be done by so that we can:
            1. avoid printing VLNV fields if their value is default (e.g. "libdefault")
            2. avoid printing VLNV name inside hierarchies
            3. insert newlines between sections, but only on the toplevel"""

            # Dictionary storing the ID sections and their default values
            id_sections = {
                "vendor": "vendor",
                "library": "libdefault",
                "name": "top",
                "version": "0.1",
            }

            id_strs = []
            section_strs = []
            for section in des:
                if section in id_sections:
                    # Never print names inside hierarchies
                    if not is_toplevel and section == "name":
                        continue
                    if des[section] != id_sections[section]:
                        id_strs.append(f"{section}: {des[section]}")
                elif section == "hierarchies":
                    section_str = f"{section}:\n"
                    for sname, sec in des["hierarchies"].items():
                        section_str += f"  {sname}:\n"
                        if is_toplevel:
                            section_str += indent(_dump_design(sec, False), "    ")[:-1]
                        else:
                            section_str += indent(_dump_design(sec, False), "    ")
                    if is_toplevel:
                        section_str += "\n"
                    section_strs.append(section_str)
                else:
                    section_strs.append(f"{section}:")
                    content = indent(
                        yaml.dump(
                            des[section],
                            Dumper=InlineYamlDumper,
                            sort_keys=False,
                            **kwargs,
                        ),
                        "  ",
                    )
                    # Don't insert newline between sections in hierarchies
                    if not is_toplevel:
                        content = content.rstrip()
                    section_strs.append(content)
            if len(id_strs) > 0:
                id_strs.append("")
                id_strs.append("")
            if not is_toplevel:
                section_strs.append("")

            # File cannot be empty - add some field to circumvent that
            if not id_strs and not section_strs:
                return "name: top"
            else:
                return "\n".join(id_strs) + "\n".join(section_strs)

        # Custom formatting for design YAMLs
        if pretty_format:
            return _dump_design(sch.dump(self))
        # Standrad formatting for IP Cores
        else:
            return yaml.dump(sch.dump(self), Dumper=InlineYamlDumper, sort_keys=True, **kwargs)

    @classmethod
    def from_yaml(cls, yaml_str: str, **kwargs: Any) -> Self:
        return cls.from_dict(yaml.safe_load(yaml_str, **kwargs))

    def save(self, path: Path, **kwargs: Any):
        with open(path, "w") as f:
            sch = self.Schema()
            sch.context[PathContext.CONTEXT_SAVE.value] = path
            sch.context[MetaKeys.SHOULD_INLINE.value] = True
            f.write(yaml.dump(sch.dump(self), Dumper=InlineYamlDumper, sort_keys=True, **kwargs))

    @classmethod
    def load(cls, path: Path, **kwargs: Any) -> Self:
        with open(path) as f:
            sch = cls.Schema()
            sch.context[PathContext.CONTEXT_LOAD.value] = path
            return cast(Self, sch.load(yaml.safe_load(f, **kwargs)))
