# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from typing import Iterable, Iterator

from typing_extensions import override

from topwrap.frontend.frontend import Frontend, FrontendMetadata
from topwrap.frontend.kpm.common import KpmFrontendParseException
from topwrap.frontend.kpm.dataflow import KpmDataflowFrontend
from topwrap.frontend.kpm.specification import KpmSpecificationFrontend
from topwrap.model.design import Design
from topwrap.model.module import Module


class KpmFrontend(Frontend):
    @property
    def metadata(self):
        return FrontendMetadata(name="kpm", file_association=[".kpm.json"])

    @override
    def parse_files(self, sources: Iterable[Path]) -> Iterator[Module]:
        specs, flows = [], []

        for src in sources:
            with open(src) as f:
                loaded = json.load(f)
                if not isinstance(loaded, dict):
                    raise KpmFrontendParseException(
                        f"Unexpected type for the KPM object '{type(loaded)}'"
                    )
                if any(k in loaded for k in ("nodes", "include", "includeGraphs")):
                    specs.append((src, loaded))
                elif "graphs" in loaded:
                    flows.append((src, loaded))
                else:
                    raise KpmFrontendParseException(
                        "Supplied file is neither a specification nor a dataflow"
                    )

        spec_front = KpmSpecificationFrontend(self.interfaces)
        spec_mods = []
        for source, spec in specs:
            spec_mods.extend(spec_front.parse(spec, source=source))
        yield from spec_mods

        flow_front = KpmDataflowFrontend([*self.modules, *spec_mods])
        for source, flow in flows:
            yield flow_front.parse(flow, source=source)

    def get_top_design(self, modules: Iterable[Module]) -> Design:
        *_, design_module = modules

        if not design_module.design:
            raise KpmFrontendParseException("Trying to get top design with no dataflow given")

        return design_module.design
