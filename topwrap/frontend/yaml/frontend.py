# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Iterable, Iterator

import yaml

from topwrap.frontend.frontend import Frontend, FrontendParseException
from topwrap.frontend.yaml.design import DesignDescriptionFrontend
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.model.module import Module


class YamlFrontend(Frontend):
    def parse_files(self, sources: Iterable[Path]) -> Iterator[Module]:
        modules = []
        designs = []

        for src in sources:
            with open(src) as f:
                loaded = yaml.safe_load(f)
                if any(k in loaded for k in ("signals", "parameters", "interfaces")):
                    modules.append(IPCoreDescriptionFrontend().parse(src))
                elif any(k in loaded for k in ("externals", "design", "ips")):
                    designs.append(src)
                else:
                    raise FrontendParseException(
                        f"{str(src)} is neither an IP Core, nor a Design Description"
                    )

        yield from modules

        for des in designs:
            yield DesignDescriptionFrontend(self.modules + modules).parse(des).parent
