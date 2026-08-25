# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Union

from topwrap.backend.kpm.common import Positions
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier, TranslationError
from topwrap.model.module import Module


@dataclass
class FrontendParseStrInput:
    name: str
    content: str


@dataclass
class FrontendMetadata:
    #: A short name for this frontend used in contexts
    #: when a specific frontend needs to be identified
    #: for example in a configuration file or CLI
    name: str

    #: File extensions associated with this frontend in the form of
    #: a set of extensions (e.g. `{".yaml", ".yml"}`)
    file_association: Iterable[str] = field(default_factory=tuple)


@dataclass
class FrontendParseOutput:
    """
    :ivar modules: Modules parsed from the input sources. A parsed module is
          included even if its identifier matches a module provided to the
          frontend during initialization.
    :ivar interfaces: Interface definitions parsed from the input sources.
    :ivar positions: Mapping from module identifiers to the positions of
          elements in their corresponding KPM graphs.
    """

    modules: list[Module] = field(default_factory=list)
    interfaces: list[InterfaceDefinition] = field(default_factory=list)
    positions: dict[Identifier, Positions] = field(default_factory=dict)


class FrontendParseException(TranslationError):
    "Exception occurred during parsing sources by the frontend"


class Frontend(ABC):
    def __init__(
        self, modules: Iterable[Module] = (), interfaces: Iterable[InterfaceDefinition] = ()
    ) -> None:
        """
        :param modules: Collection of predefined module definitions
            that can be used by a frontend.
        :param interfaces: Collection of predefined interface definitions
            that can be used by a frontend.
        """

        super().__init__()
        self.modules = list(modules)
        self.interfaces = list(interfaces)

    def parse_str(
        self, sources: Iterable[Union[str, FrontendParseStrInput]]
    ) -> FrontendParseOutput:
        """
        Parse a collection of string sources into IR modules

        :param sources: Iterable of string sources. Items can either
            be a plain `str` with the content or the `FrontendParseStrInput`
            dataclass where additional parameters related to the source
            can be specified.
        """

        files = []
        for src in sources:
            if isinstance(src, FrontendParseStrInput):
                file = NamedTemporaryFile("w+", prefix=src.name)
                file.write(src.content)
            else:
                file = NamedTemporaryFile("w+")
                file.write(src)
            file.flush()
            files.append(file)
        out = self.parse_files([Path(f.name) for f in files])
        for f in files:
            f.close()
        return out

    @property
    @abstractmethod
    def metadata(self) -> FrontendMetadata:
        "Return metadata about this frontend such as its file associations"

    @abstractmethod
    def parse_files(
        self, sources: Iterable[Path], *, include_dirs: Iterable[Path] = ()
    ) -> FrontendParseOutput:
        """
        Parse a collection of source files into IR modules

        :param sources: Collection of paths to sources
        """
