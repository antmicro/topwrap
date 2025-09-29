# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Iterable, Type

from topwrap.frontend.frontend import Frontend, FrontendMetadata, FrontendParseOutput
from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module


@dataclass
class UnknownInfoOutput:
    parsed: FrontendParseOutput
    unknown_sources: list[Path]


class AutomaticFrontend(Frontend):
    """
    This class can automatically dispatch files to appropriate
    frontends based on the file extension
    """

    _unknown_sources: list[Path]

    @property
    def metadata(self):
        return FrontendMetadata(name="automatic")

    def parse_files(self, sources: Iterable[Path]) -> FrontendParseOutput:
        self._unknown_sources = []
        split = dict[Type[Frontend], list[Path]]()

        for source in sources:
            for ext, frontend in FrontendRegistry.FILE_ASSOCIATIONS.items():
                if str(source).lower().endswith(ext):
                    split.setdefault(frontend, []).append(source)
                    break
            else:
                self._unknown_sources.append(source)

        modules = list[Module]()
        interfaces = list[InterfaceDefinition]()

        for frontend, sources in split.items():
            frontend_output = frontend(
                modules=self.modules, interfaces=self.interfaces
            ).parse_files(sources)
            modules.extend(frontend_output.modules)
            interfaces.extend(frontend_output.interfaces)

        return FrontendParseOutput(modules=modules, interfaces=interfaces)

    def parse_files_with_unknown_info(self, sources: Iterable[Path]) -> UnknownInfoOutput:
        """
        Parse an iterable of sources just like :py:meth:`parse_files`,
        but return additional information about files that weren't matched
        to any existing frontend and thus weren't parsed.
        """

        parsed = self.parse_files(sources)
        return UnknownInfoOutput(parsed, self._unknown_sources)


class FrontendRegistry:
    FRONTENDS: ClassVar[list[type[Frontend]]] = [
        SystemVerilogFrontend,
        YamlFrontend,
        KpmFrontend,
        AutomaticFrontend,
    ]

    FILE_ASSOCIATIONS: ClassVar[dict[str, Type["Frontend"]]] = {}
    BY_NAME: ClassVar[dict[str, Type["Frontend"]]] = {}

    @classmethod
    def initialize(cls):
        for frontend in cls.FRONTENDS:
            meta = frontend().metadata
            cls.BY_NAME[meta.name] = frontend
            for ext in meta.file_association:
                cls.FILE_ASSOCIATIONS[ext] = frontend


FrontendRegistry.initialize()
