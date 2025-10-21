# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Iterable, List, Optional

import yaml
from typing_extensions import override

from topwrap.cli import load_interfaces_from_repos
from topwrap.frontend.automatic import AutomaticFrontend
from topwrap.frontend.frontend import Frontend
from topwrap.model.inference.inference import infer_interfaces_from_module, parse_grouping_hints
from topwrap.model.inference.mapping import InterfacePortMappingDefinition
from topwrap.model.misc import Identifier
from topwrap.repo.files import File
from topwrap.repo.resource import FileHandler, Resource
from topwrap.repo.user_repo import (
    Core,
    InterfaceDescription,
    InterfaceMapping,
    ResourcePathWithType,
)
from topwrap.resource_field import FileReferenceHandler

logger = logging.getLogger(__name__)


class CoreFileHandler(FileHandler):
    """
    Implementation of FileHandler for various files that can be parsed into
    IR modules using one of the frontends. This handler emits :class:`Core`
    resources that can be later saved into a user repository.
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
        modules = self.frontend.parse_files(f.path for f in self._files).modules

        for mod in modules:
            if (
                mod.id.name not in self.tops
                and mod.id.combined() not in self.tops
                and len(self.tops) > 0
            ):
                continue

            if not self.all_sources:
                deps = set(FileReferenceHandler(f.file) for m in mod.hierarchy() for f in m.refs)
            else:
                deps = (FileReferenceHandler(f.path) for f in self._files)

            if not isinstance(self.frontend, AutomaticFrontend):
                deps = [ResourcePathWithType(d, self.frontend.metadata.name) for d in deps]

            res_name = mod.id.combined().removeprefix(Identifier("").combined())
            resources.append(Core(name=res_name, top_level_name=mod.id.name, sources=list(deps)))

            if self.inference:
                [*intf_defs] = load_interfaces_from_repos()

                cand_intf_defs = intf_defs
                if self.inference_interfaces:
                    cand_intf_defs = [
                        x for x in intf_defs if x.id.name in self.inference_interfaces
                    ]

                mapping = infer_interfaces_from_module(
                    mod,
                    cand_intf_defs,
                    grouping_hints=parse_grouping_hints(self.grouping_hints),
                )

                if mapping.interfaces:
                    resources.append(
                        InterfaceMapping(
                            name=mod.id.combined(),
                            definition=InterfacePortMappingDefinition([mapping]),
                        )
                    )

        return resources


class InterfaceFileHandler(FileHandler):
    def __init__(self, files: List[File]):
        self._files = files

    @override
    def parse(self) -> List[Resource]:
        resources: List[Resource] = []
        for f in self._files:
            with open(f.path) as fd:
                data = yaml.safe_load(fd)
            name = data["name"]
            iface_desc = InterfaceDescription(name, f)
            resources.append(iface_desc)
        return resources
