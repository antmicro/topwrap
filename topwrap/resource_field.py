# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Collection, Type, Union

from topwrap.repo.files import HttpGetFile
from topwrap.repo.resource import ResourceType
from topwrap.util import UnreachableError, get_config, path_relative_to


class InvalidIdentifierException(Exception):
    pass


class InvalidArgumentException(Exception):
    pass


class PathContext(Enum):
    CONTEXT_LOAD = "__load_path"
    CONTEXT_SAVE = "__save_path"


ARG_SEPARATOR = "|"


class ResourceReferenceHandler(ABC):
    """Base class for implementing handlers for custom schemes in our
    resource reference strings. Its main responsibility is to convert the
    scheme, args and value groups into a filesystem path, where these groups
    are parsed from the string as follows:

    `scheme[arg1|arg2]:value`
    """

    scheme: ClassVar[str]

    value: str
    args: Collection[str]
    meta: dict[str, Any]

    def __init__(self, value: str, args: Collection[str] = [], /):
        self.value = value
        self.args = args
        self.meta = {}

    def update_meta(self, meta: dict[str, Any]):
        self.meta.update(meta)

    @abstractmethod
    def to_path(self) -> Path:
        raise NotImplementedError

    def _join_args(self) -> str:
        for arg in self.args:
            if ARG_SEPARATOR in arg:
                raise InvalidArgumentException
        return ARG_SEPARATOR.join(self.args)

    def to_str(self) -> str:
        if self.args:
            return f"{self.scheme}[{self._join_args()}]:{self.value}"
        else:
            return f"{self.scheme}:{self.value}"


class UriReferenceHandler(ResourceReferenceHandler):
    scheme = "get"

    def to_path(self) -> Path:
        return HttpGetFile(self.value).path


class FileReferenceHandler(ResourceReferenceHandler):
    scheme = "file"

    def __init__(self, value: Union[str, Path], args: Collection[str] = []):
        super().__init__(str(value), args)

    def to_path(self) -> Path:
        base_path = self.meta.get(PathContext.CONTEXT_LOAD.value, Path())
        if not isinstance(base_path, Path):
            raise UnreachableError
        return Path(os.path.normpath(base_path.parent / self.value))

    def to_str(self) -> str:
        save_path = self.meta.get(PathContext.CONTEXT_SAVE.value, Path())
        if not isinstance(save_path, Path):
            raise UnreachableError
        rel_path = str(path_relative_to(self.to_path().resolve(), save_path.parent.resolve()))
        return f"{self.scheme}:{rel_path}"


class RepoReferenceHandler(ResourceReferenceHandler):
    scheme = "repo"

    def to_path(self) -> Path:
        [repo_name] = self.args
        repo_path = get_config().repositories.get(repo_name)
        if repo_path is None:
            raise ValueError(f"Could not find repo '{repo_name}'")
        return repo_path.to_path() / self.value

    def to_resource(self, type: type[ResourceType]) -> ResourceType:
        [repo_name] = self.args
        repo = get_config().loaded_repos.get(repo_name)
        if repo is None:
            raise ValueError(f"Could not find repo '{repo_name}'")
        return repo.get_resource(type, self.value)


class SupportedSchemeGroup:
    """The generic parser for resource reference strings and
    the dispatcher for concrete supported scheme handlers"""

    _IDENT_REGEX = re.compile(r"^([^[]+?)(?:\[(.*?)\])?:(.*)$")
    handlers: Collection[Type[ResourceReferenceHandler]]

    @classmethod
    def parse(cls, ident: str) -> ResourceReferenceHandler:
        match = re.match(cls._IDENT_REGEX, ident)
        if match is None:
            raise InvalidIdentifierException(
                f"Invalid resource identifier: '{ident}'. It has to match regex"
                f" {cls._IDENT_REGEX.pattern}"
            )
        scheme, args, path = match.groups()
        if not isinstance(scheme, str) or not isinstance(path, str):
            raise InvalidIdentifierException(f"Missing scheme or path in '{ident}'")
        args = [] if args is None else args.split("|")
        for handler in cls.handlers:
            if handler.scheme == scheme:
                return handler(path, args)
        raise InvalidIdentifierException(
            f"Unsupported resource scheme: '{scheme}' in identifier: '{ident}'"
        )


class YamlCommonSchemes(SupportedSchemeGroup):
    """Resource reference schemes supported inside our
    YAML files"""

    handlers = [UriReferenceHandler, FileReferenceHandler, RepoReferenceHandler]
