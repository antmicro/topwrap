# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Type, cast

from topwrap.repo.resource import FileHandler, Resource, ResourceHandler, ResourceType

logger = logging.getLogger(__name__)

ParseHandler = Callable[..., List[Resource]]
RepoParseHandlers = Dict[Enum, ParseHandler]
RepoResourceHandlers = Dict[ResourceType, ResourceHandler[ResourceType]]


class ResourceNotSupportedException(Exception):
    """Raised when a resource is not supported"""


class Repo:
    """Base class for implementing user repository"""

    def __init__(self, resource_handlers: List[ResourceHandler[Resource]]) -> None:
        self.resources: Dict[Type[Resource], List[Resource]] = defaultdict(list)
        self.resource_handlers = {}
        for handler in resource_handlers:
            self.resource_handlers[handler.resource_type] = handler

    def add_files(self, handler: FileHandler) -> None:
        """Parses resources available in files and adds them to the repository"""
        resources = handler.parse()
        logger.info(f"Repo.add_file: Obtained {len(resources)} resources from {handler}")
        for resource in resources:
            self.add_resource(resource)

    def add_resource(self, resource: Resource) -> None:
        """Adds a single resource to the repository"""
        self.resources[type(resource)] += [resource]

    def get_resources(self, type: Type[ResourceType]) -> List[ResourceType]:
        """Implements the same operation as self.resources[type] but gives correct hints to the
        typechecker"""
        return cast(List[ResourceType], self.resources[type])

    def load(self, repo_path: Path, **kwargs: Any) -> None:
        """Loads repository from repo_path"""
        for handler in self.resource_handlers.values():
            resources = handler.load(Path(repo_path).expanduser())
            for resource in resources:
                self.add_resource(resource)

        logger.info(f"Repo.load: Loaded {len(self.resources.values())} resources from {repo_path}")

    def save(self, dest: Path, **kwargs: Any) -> None:
        """Saves repository to dest"""
        for res_type_value in self.resources.values():
            for res in res_type_value:
                if type(res) not in self.resource_handlers:
                    raise ResourceNotSupportedException(
                        "A resource not supported by this repository. "
                        "Add a new resource handler to UserRepo.resource_handlers"
                    )
                self.resource_handlers[type(res)].save(res, repo_path=dest, **kwargs)
        logger.info(
            f"Repo.save: Saved {len(self.resources.values())} resources to {dest} repository"
        )
