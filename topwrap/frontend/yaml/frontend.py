# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

import yaml

from topwrap.frontend.frontend import (
    Frontend,
    FrontendMetadata,
    FrontendParseException,
    FrontendParseOutput,
    FrontendParseStrInput,
)
from topwrap.frontend.yaml.design import DesignDescriptionFrontend
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.model.module import Module


class YamlFrontend(Frontend):
    @property
    def metadata(self):
        return FrontendMetadata(name="yaml", file_association=[".yaml", ".yml"])

    def _parse_source(
        self,
        ip_core_method: Callable[[IPCoreDescriptionFrontend, Any], Module],
        name: str,
        src: Union[str, Path],
        loaded: Any,
    ) -> tuple[Optional[Module], Optional[Union[str, Path]]]:
        if any(k in loaded for k in ("signals", "parameters", "interfaces")):
            return (ip_core_method(IPCoreDescriptionFrontend(), src), None)
        elif any(k in loaded for k in ("externals", "design", "ips")):
            return (None, src)
        else:
            raise FrontendParseException(f"{name} is neither an IP Core, nor a Design Description")

    def parse_files(self, sources: Iterable[Path]) -> FrontendParseOutput:
        modules = list[Module]()
        designs = []

        for src in sources:
            with open(src) as f:
                [module, design] = self._parse_source(
                    IPCoreDescriptionFrontend.parse_file, str(src), src, yaml.safe_load(f)
                )
                if module:
                    modules.append(module)
                if design:
                    designs.append(design)

        for des in designs:
            modules.append(DesignDescriptionFrontend(self.modules + modules).parse_file(des).parent)
        return FrontendParseOutput(modules=modules)

    def parse_str(
        self, sources: Iterable[Union[str, FrontendParseStrInput]]
    ) -> FrontendParseOutput:
        modules = list[Module]()
        designs = []

        for src in sources:
            if isinstance(src, str):
                [module, design] = self._parse_source(
                    IPCoreDescriptionFrontend.parse_str, "<input string>", src, yaml.safe_load(src)
                )
            else:
                [module, design] = self._parse_source(
                    IPCoreDescriptionFrontend.parse_str,
                    src.name,
                    src.content,
                    yaml.safe_load(src.content),
                )
            if module:
                modules.append(module)
            if design:
                designs.append(design)

        for des in designs:
            modules.append(DesignDescriptionFrontend(self.modules + modules).parse_str(des).parent)

        return FrontendParseOutput(modules=modules, interfaces=[])
