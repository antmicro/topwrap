# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""
This is an incomplete (and partially incorrect) schema for
CAPI2 https://fusesoc.readthedocs.io/en/stable/ref/capi2.html

It is meant to be iterated on and extended as the need arises.
As of now, the "schema" is only used for serialization.
"""

from typing import Any, ClassVar, Type, Union, cast

import yaml
from marshmallow import Schema as MarshmallowSchema
from marshmallow import post_dump
from marshmallow_dataclass import dataclass


def remove_empty(data: Any, *_: Any, **__: Any) -> object:
    """
    A common cleanup method for the FuseSoc .core output.
    Neither null, empty lists or empty dicts should be a part of the serialized output.
    """
    if not isinstance(data, dict):
        return data

    data = cast(dict[str, Any], data)
    for key in list(data.keys()):
        if data[key] is None or (
            (isinstance(data[key], list) or isinstance(data[key], dict)) and not data[key]
        ):
            del data[key]

    return data


def wrap_by(key: str, data: Any, *_: Any, **__: Any) -> object:
    """
    This utility helps in converting certain structures to the correct output.
    For example, this pattern exists in .core-files:

    ```yaml
    items:
        - foo: { x: ... }
        - bar: { x: ... }
    ```

    Which is more conveniently expressed as

    ```python
    @dataclass
    class Item:
        name: str # maps to foo/bar
        x: str

    @dataclass
    class Top:
        items: list[Item]
    ```

    Using `wrap_by("name", ...)` in `Item` during `post_dump` helps to convert between these.
    """

    if not isinstance(data, dict):
        return data

    data = cast(dict[str, Any], data)

    if key in data:
        name = data[key]
        del data[key]
        return {name: data}
    return data


@dataclass
class VLNV_S:
    vendor: str
    library: str
    name: str
    version: str

    @post_dump
    def stringify(_, data: dict[str, str], **__: Any) -> str:
        if data["version"]:
            return f"{data['vendor']}:{data['library']}:{data['name']}:{data['version']}"
        return f"{data['vendor']}:{data['library']}:{data['name']}"


@dataclass
class FileSource:
    name: str
    file_type: str

    @post_dump
    def post_process(_, *args: Any, **kwargs: Any):
        return wrap_by("name", *args, **kwargs)


@dataclass
class FileSet:
    files: list[FileSource]
    depend: list[VLNV_S]

    @post_dump
    def post_process(_, *args: Any, **kwargs: Any):
        return remove_empty(*args, **kwargs)


Hooks = dict[str, list[str]]


@dataclass
class TargetCommon:
    filesets: list[str]
    toplevel: str
    hooks: Hooks

    @post_dump
    def post_process(_, *args: Any, **kwargs: Any):
        return remove_empty(*args, **kwargs)


@dataclass
class ToolTarget(TargetCommon):
    default_tool: str
    tools: dict[str, Any]


@dataclass
class FlowTarget(TargetCommon):
    flow: str
    flow_options: dict[str, Any]


Target = Union[ToolTarget, FlowTarget]


@dataclass
class Script:
    cmd: list[str]


@dataclass
class Core:
    name: VLNV_S
    description: str
    filesets: dict[str, FileSet]
    targets: dict[str, Target]
    scripts: dict[str, Script]
    Schema: ClassVar[Type[MarshmallowSchema]] = MarshmallowSchema

    @post_dump
    def post_process(_, *args: Any, **kwargs: Any):
        return remove_empty(*args, **kwargs)

    def _to_yaml_section(self) -> str:
        obj = self.__class__.Schema().dump(self)
        src = yaml.dump(obj, indent=4, default_flow_style=False, sort_keys=False)
        return src

    def to_yaml(self) -> str:
        header = "CAPI=2:"
        return f"{header}\n{self._to_yaml_section()}"
