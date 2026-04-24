# Copyright (c) 2024-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Union

import marshmallow
import marshmallow_dataclass
from typing_extensions import override

from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.backend.yaml.common.interface_schema import (
    InterfaceDefinitionDescription,
)
from topwrap.backend.yaml.interface import InterfaceDefinitionDescriptionBackend
from topwrap.common_serdes import (
    ResourcePathT,
)
from topwrap.frontend.automatic import FrontendRegistry
from topwrap.frontend.yaml.interface import InterfaceDefinitionDescriptionFrontend
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module
from topwrap.repo.repo import Repo
from topwrap.repo.resource import Resource, ResourceHandler

logger = logging.getLogger(__name__)


@marshmallow_dataclass.dataclass
class ResourcePathWithType:
    resource: ResourcePathT
    type: str

    @marshmallow.validates("type")
    def _type_validator(self, value: str):
        assert value in FrontendRegistry.BY_NAME


class Core(Resource):
    """Represents a hardware core resource"""

    top_or_source_yaml: Union[Module, Path]

    def __init__(self, name: str, top_or_source_yaml: Union[Module, Path]):
        # YAML can't be parsed during the loading of the resource. The interface in the module
        # needs to load InterfaceDefinition to check if the YAML doesn't have errors. While
        # loading InterfaceDefinition, all repos are loaded, which triggers the loading of
        # the Core resource. To fix this, the YAML is lazy-loaded. However, source_yaml can't
        # be delivered when the Core is added to the repo from HDL sources that can only
        # supply the IR Module.
        super().__init__(name)
        self.top_or_source_yaml = top_or_source_yaml

    @property
    def top(self) -> Module:
        """
        Returns loaded IR Module or load it from YAML if not loaded
        """
        if isinstance(self.top_or_source_yaml, Module):
            return self.top_or_source_yaml
        else:
            self.top_or_source_yaml = IPCoreDescriptionFrontend().parse_file(
                self.top_or_source_yaml
            )
        return self.top_or_source_yaml

    @property
    def existing_ifaces(self) -> Iterator[InterfaceDefinition]:
        for iface in self.top.interfaces:
            yield iface.definition


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

        backend = IpCoreDescriptionBackend()
        representation = backend.represent(res.top)
        output_info = next(backend.serialize(representation))

        with open(core_dir / "module.yaml", "w") as f:
            f.write(output_info.content)

    @override
    def load(self, repo_path: Path) -> Iterator[Core]:
        """Handles a core-specific load action"""

        cores_dir = repo_path / self._cores_rel_dir
        if not cores_dir.exists():
            return
        for core_dir in cores_dir.iterdir():
            if not core_dir.is_dir():
                continue
            try:
                name = core_dir.name
                yield Core(name, top_or_source_yaml=core_dir / "module.yaml")
            except Exception as e:
                logger.warning(
                    f'Couldn\'t load core resource stored in "{core_dir.absolute()}": {e}'
                )


@dataclass
class InterfaceDefinitionResource(Resource):
    """Represents an interface description resource"""

    definition: InterfaceDefinition

    def __init__(self, definition: InterfaceDefinition):
        super().__init__(definition.id.combined())
        self.definition = definition


class InterfaceDescriptionHandler(ResourceHandler[InterfaceDefinitionResource]):
    """Class that can operate on InterfaceDefinitionResource resources"""

    resource_type = InterfaceDefinitionResource
    _ifaces_rel_dir = Path("interfaces")

    @override
    def save(self, res: InterfaceDefinitionResource, repo_path: Path) -> None:
        """Handles interface-specific save action"""
        ifaces_dir = repo_path / self._ifaces_rel_dir
        ifaces_dir.mkdir(parents=True, exist_ok=True)

        iface_def = InterfaceDefinitionDescriptionBackend().represent(res.definition)
        iface_def.save(ifaces_dir / (res.definition.id.combined() + ".yaml"))

    @override
    def load(self, repo_path: Path) -> Iterator[InterfaceDefinitionResource]:
        """Handles interface-specific load action"""
        ifaces_dir = repo_path / self._ifaces_rel_dir
        if not ifaces_dir.exists():
            return

        for iface_file in ifaces_dir.iterdir():
            if iface_file.is_dir():
                continue
            try:
                with open(iface_file, "r") as f:
                    iface_def = InterfaceDefinitionDescription.from_yaml(f.read())
                    yield InterfaceDefinitionResource(
                        InterfaceDefinitionDescriptionFrontend().parse(iface_def)
                    )
            except Exception as e:
                logger.warning(
                    "Couldn't load interface definition resource stored in "
                    f'"{iface_file.absolute()}": {e}'
                )


class UserRepo(Repo):
    def __init__(self, name: str):
        resource_handlers = [
            CoreHandler(),
            InterfaceDescriptionHandler(),
        ]
        super().__init__(resource_handlers, name)

    def get_core_by_name(self, name: str) -> Optional[Core]:
        return next((c for c in self.get_resources(Core) if c.name == name), None)
