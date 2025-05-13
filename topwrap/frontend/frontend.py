# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Iterator

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import TranslationError
from topwrap.model.module import Module


class FrontendParseException(TranslationError):
    "Exception occurred during parsing sources by the frontend"


class Frontend(ABC):
    def __init__(
        self, modules: Iterable[Module] = (), interfaces: Iterable[InterfaceDefinition] = ()
    ) -> None:
        """
        :param modules: Collection of preloaded modules that may have
            been utilized by the subsequent frontend data formats.
        :param interfaces: Collection of preloaded interface definitions
            that may have been used by the subsequent frontend data formats.
        """

        super().__init__()
        self.modules = list(modules)
        self.interfaces = list(interfaces)

    def parse_str(self, sources: Iterable[str]) -> Iterator[Module]:
        """
        Parse a collection of string sources into IR modules

        :param sources: Collection of string sources
        """

        files = []
        for src in sources:
            file = NamedTemporaryFile("w+")
            file.write(src)
            files.append(file)
        yield from self.parse_files([Path(f.name) for f in files])
        for f in files:
            f.close()

    @abstractmethod
    def parse_files(self, sources: Iterable[Path]) -> Iterator[Module]:
        """
        Parse a collection of source files into IR modules

        :param sources: Collection of paths to sources
        """
