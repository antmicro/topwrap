# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Iterable, List, Optional

from typing_extensions import override

from topwrap.cli import load_interfaces_from_repos
from topwrap.frontend.automatic import AutomaticFrontend
from topwrap.frontend.frontend import Frontend
from topwrap.model.inference.inference import infer_interfaces_from_module, parse_grouping_hints
from topwrap.model.inference.mapping import (
    InterfacePortMapping,
    map_interfaces_to_module,
)
from topwrap.repo.files import File
from topwrap.repo.resource import FileHandler, Resource
from topwrap.repo.user_repo import (
    Core,
    InterfaceDefinitionResource,
)

logger = logging.getLogger(__name__)


class ModuleFileHandler(FileHandler):
    """
    Implementation of FileHandler for various files that can be parsed into
    IR :class:`Module`'s using one of the frontends. This handler emits :class:`Core` and
    :class:`InterfaceDefinitionResource` resources that can be later saved into a user repository.
    """

    def __init__(
        self,
        files: List[File],
        frontend: Optional[Frontend] = None,
        tops: Iterable[str] = (),
        all_sources: bool = False,
        inference: bool = False,
        inference_interfaces: Iterable[str] = [],
        grouping_hints: Iterable[str] = [],
    ):
        super().__init__(files)
        self.frontend = AutomaticFrontend() if frontend is None else frontend
        self.tops = set(tops)
        self.all_sources = all_sources
        self.inference = inference
        self.inference_interfaces = inference_interfaces
        self.grouping_hints = grouping_hints

    @override
    def parse(self) -> List[Resource]:
        resources: List[Resource] = []
        frontend_output = self.frontend.parse_files(f.path for f in self._files)

        for mod in frontend_output.modules:
            if (
                mod.id.name not in self.tops
                and mod.id.combined() not in self.tops
                and len(self.tops) > 0
            ):
                continue

            [*intf_defs] = load_interfaces_from_repos()
            cand_intf_defs = intf_defs
            if self.inference_interfaces:
                cand_intf_defs = [
                    x
                    for x in intf_defs
                    if (x.id.name in self.inference_interfaces)
                    or (x.id.combined() in self.inference_interfaces)
                ]

            mapping: InterfacePortMapping = infer_interfaces_from_module(
                mod,
                cand_intf_defs,
                grouping_hints=parse_grouping_hints(self.grouping_hints),
            )  # mapping to interface port mapping definition
            map_interfaces_to_module([mapping], cand_intf_defs, mod)

            resources.append(Core(mod.id.name, top_or_source_yaml=mod))

        for iface in frontend_output.interfaces:
            resources.append(InterfaceDefinitionResource(iface))

        return resources
