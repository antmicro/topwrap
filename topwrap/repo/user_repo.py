# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Type, Union

import marshmallow
import marshmallow_dataclass
from typing_extensions import override

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    ResourcePathT,
    ext_field,
)
from topwrap.frontend.automatic import AutomaticFrontend, FrontendRegistry
from topwrap.frontend.frontend import Frontend
from topwrap.model.module import Module
from topwrap.repo.exceptions import TopLevelNotFoundException
from topwrap.repo.files import File, LocalFile
from topwrap.repo.repo import ExistsStrategy, Repo
from topwrap.repo.resource import Resource, ResourceHandler
from topwrap.resource_field import FileReferenceHandler

logger = logging.getLogger(__name__)


@marshmallow_dataclass.dataclass
class ResourcePathWithType:
    resource: ResourcePathT
    type: str

    @marshmallow.validates("type")
    def _type_validator(self, value: str):
        assert value in FrontendRegistry.BY_NAME


@dataclass
class LoadedCore:
    "Returned by :meth:`Core.ir_module`"

    top_level: Module
    other_sources: Iterable[Module]
    unknown_sources: Iterable[Path]


@marshmallow_dataclass.dataclass
class Core(Resource, MarshmallowDataclassExtensions):
    """Represents a hardware core resource"""

    #: A custom name for the core resource
    #: Usually based on :attr:`top_level_name`
    name: str

    #: The exact name of the top-level module that this core
    #: represents as it exists in the sources
    top_level_name: str

    sources: List[Union[ResourcePathWithType, ResourcePathT]]

    #: Whether this core packs its own sources or
    #: just references external ones
    by_ref: bool = ext_field(False, load_only=True)

    @cached_property
    def ir_module(self) -> LoadedCore:
        frontends = dict[Type[Frontend], list[Path]]()
        for src in self.sources:
            front = (
                FrontendRegistry.BY_NAME[src.type]
                if isinstance(src, ResourcePathWithType)
                else AutomaticFrontend
            )
            srcpath = (src.resource if isinstance(src, ResourcePathWithType) else src).to_path()
            frontends.setdefault(front, []).append(srcpath)
        mods = []
        unknowns = set()
        top = None
        for front, srcs in frontends.items():
            if issubclass(front, AutomaticFrontend):
                info = front(modules=mods).parse_files_with_unknown_info(srcs)
                modules = info.modules
                unknowns.update(info.unknown_sources)
            else:
                modules = front(modules=mods).parse_files(srcs)
            for mod in modules:
                if mod.id.name == self.top_level_name:
                    top = mod
                else:
                    mods.append(mod)
        if top is None:
            raise TopLevelNotFoundException(self)

        return LoadedCore(top, mods, unknowns)


class CoreHandler(ResourceHandler[Core]):
    """Class that can operate on Core resources"""

    resource_type = Core
    _cores_rel_dir = Path("cores")
    _srcs_dir_name = "srcs"

    @override
    def save(self, res: Core, repo_path: Path) -> None:
        """Handles a core-specific save action"""
        core_dir = repo_path / self._cores_rel_dir / res.name
        core_dir.mkdir(parents=True, exist_ok=True)
        path_to_save = core_dir / ".core.yaml"

        if path_to_save.exists():
            # This resource was already saved
            return

        if not res.by_ref:
            srcs = []
            src_dir = core_dir / self._srcs_dir_name
            src_dir.mkdir(exist_ok=True)
            for src in res.sources:
                path = (src.resource if isinstance(src, ResourcePathWithType) else src).to_path()
                target = src_dir / path.name
                ref = FileReferenceHandler(target)
                if isinstance(src, ResourcePathWithType):
                    srcs.append(ResourcePathWithType(resource=ref, type=src.type))
                else:
                    srcs.append(ref)
                if path != target:
                    shutil.copy(path, target)
            res.sources = srcs

        res.save(path_to_save)

    @override
    def load(self, repo_path: Path) -> Iterator[Core]:
        """Handles a core-specific load action"""

        cores_dir = repo_path / self._cores_rel_dir
        yield from (Core.load(path) for path in cores_dir.glob("*/*.core.yaml"))


@dataclass
class InterfaceDescription(Resource):
    """Represents an interface description resource"""

    name: str
    file: File


class InterfaceDescriptionHandler(ResourceHandler[InterfaceDescription]):
    """Class that can operate on InterfaceDescription resources"""

    resource_type = InterfaceDescription
    _ifaces_rel_dir = Path("interfaces")

    @override
    def save(self, res: InterfaceDescription, repo_path: Path) -> None:
        """Handles interface-specific save action"""
        ifaces_dir = repo_path / self._ifaces_rel_dir
        ifaces_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"InterfaceDescriptionHandler.save: Saving {res.name} in {ifaces_dir}")
        output_path = ifaces_dir / res.file.path.name
        res.file.copy(output_path, ExistsStrategy.SKIP)
        logger.debug(f"InterfaceDescriptionHandler.save: Copied {res.name} to {output_path}")

    @override
    def load(self, repo_path: Path) -> Iterator[InterfaceDescription]:
        """Handles interface-specific load action"""
        ifaces_dir = repo_path / self._ifaces_rel_dir

        yaml_files = []
        for ext in ["*.yml", "*.yaml"]:
            for f in ifaces_dir.glob(ext):
                yaml_files.append(f)
        logger.debug(
            f"InterfaceDescriptionHandler.load: Found {len(yaml_files)} files in {ifaces_dir}"
        )

        for yaml_file in yaml_files:
            iface_name = yaml_file.stem
            iface = InterfaceDescription(iface_name, LocalFile(yaml_file))
            yield iface


class UserRepo(Repo):
    def __init__(self, name: str):
        resource_handlers = [
            CoreHandler(),
            InterfaceDescriptionHandler(),
        ]
        super().__init__(resource_handlers, name)

    def get_core_by_name(self, name: str) -> Optional[Core]:
        return next((c for c in self.get_resources(Core) if c.name == name), None)
