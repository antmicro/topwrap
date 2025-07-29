# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Iterator, Union

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import TranslationError
from topwrap.model.module import Module


@dataclass
class FrontendParseStrInput:
    name: str
    content: str


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

    def parse_str(self, sources: Iterable[Union[str, FrontendParseStrInput]]) -> Iterator[Module]:
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
        yield from self.parse_files([Path(f.name) for f in files])
        for f in files:
            f.close()

    @abstractmethod
    def parse_files(self, sources: Iterable[Path]) -> Iterator[Module]:
        """
        Parse a collection of source files into IR modules

        :param sources: Collection of paths to sources
        """
