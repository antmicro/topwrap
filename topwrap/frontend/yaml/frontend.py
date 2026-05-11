# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Iterable, Union

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

logger = logging.getLogger(__name__)


class YamlFrontend(Frontend):
    @property
    def metadata(self):
        return FrontendMetadata(name="yaml", file_association=[".yaml", ".yml"])

    def detect_description_type(self, src: str, filename: str) -> str:
        loaded = yaml.safe_load(src)
        if any(k in loaded for k in ("signals", "parameters", "ports", "interfaces")):
            return "ip_core"
        elif any(k in loaded for k in ("external", "connections", "ips")):
            return "design_description"
        else:
            raise FrontendParseException(f"{src} is neither an IP Core, nor a Design Description")

    def parse_design_file(self, source: Path) -> FrontendParseOutput:
        modules = list[Module]()

        ir_des = DesignDescriptionFrontend(self.modules + modules).parse_file(source)
        ir_des.update_interconnects_from_memory_maps()
        modules.append(ir_des.parent)

        return FrontendParseOutput(modules=modules)

    def parse_module_files(self, sources: Iterable[Path]) -> FrontendParseOutput:
        modules = list[Module]()

        for src in sources:
            modules.append(IPCoreDescriptionFrontend.parse_file(IPCoreDescriptionFrontend(), src))
        return FrontendParseOutput(modules=modules)

    def parse_files(self, sources: Iterable[Path]) -> FrontendParseOutput:
        modules = list[Module]()
        designs = list[Path]()

        for src in sources:
            logger.debug("Parsing file {}".format(src))
            with open(src) as f:
                if self.detect_description_type(f.read(), src.name) == "design_description":
                    designs.append(src)
                else:
                    modules.extend(self.parse_module_files([src]).modules)

        for des in designs:
            logger.info("Analyzing source {}".format(des))
            modules.extend(self.parse_design_file(des).modules)
            params = modules[-1].parameters
            ports = modules[-1].ports
            interfaces = modules[-1].interfaces
            for p in params:
                logger.info("Found parameter {}".format(p.name))
            for p in ports:
                logger.info("Found port {} {}".format(p.name, p.direction.name))
            for i in interfaces:
                logger.info("Found interface {}".format(i.name))

        return FrontendParseOutput(modules=modules)

    def parse_str(
        self, sources: Iterable[Union[str, FrontendParseStrInput]]
    ) -> FrontendParseOutput:
        modules = list[Module]()
        designs = []

        for src in sources:
            content = src.content if isinstance(src, FrontendParseStrInput) else src
            name = src.name if isinstance(src, FrontendParseStrInput) else "<input string>"

            if self.detect_description_type(content, name) == "design_description":
                designs.append(content)
            else:
                modules.append(
                    IPCoreDescriptionFrontend.parse_str(IPCoreDescriptionFrontend(), content)
                )

        for des in designs:
            modules.append(DesignDescriptionFrontend(self.modules + modules).parse_str(des).parent)

        return FrontendParseOutput(modules=modules, interfaces=[])
