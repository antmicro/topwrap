# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from enum import Enum
from os import PathLike
from typing import Callable, Dict, List, Type

from topwrap.repo.resource import FileHandler, Resource, ResourceHandler

logger = logging.getLogger(__name__)

ParseHandler = Callable[..., List[Resource]]
RepoParseHandlers = Dict[Enum, ParseHandler]
RepoResourceHandlers = Dict[Type[Resource], ResourceHandler]


class ResourceNotSupportedException(Exception):
    """Raised when a resource is not supported"""


class Repo:
    """Base class for implementing user repository"""

    def __init__(self, resource_handlers: List[ResourceHandler]) -> None:
        self.resources: List[Resource] = []
        self.resource_handlers = {}
        for handler in resource_handlers:
            self.resource_handlers[handler.resource_type] = handler

    def add_files(self, handler: FileHandler) -> None:
        """Parses resources available in files and adds them to the repository"""
        resources = handler.parse()
        logger.info(f"Repo.add_file: Obtained {len(resources)} resources from {handler}")
        for resource in resources:
            self.add_resource(resource)

    def add_resource(self, res: Resource) -> None:
        """Adds resource to the repository"""
        self.resources.append(res)

    def load(self, repo_path: PathLike, **kwargs) -> None:
        """Loads repository from repo_path"""

        resources = []
        for handler in self.resource_handlers.values():
            resources.extend(handler.load(repo_path))
        logger.info(f"Repo.load: Loaded {len(resources)} resources from {repo_path}")
        self.resources.extend(resources)

    def save(self, dest: PathLike, **kwargs) -> None:
        """Saves repository to dest"""

        for res in self.resources:
            res_type = type(res)
            if res_type not in self.resource_handlers:
                raise ResourceNotSupportedException(
                    "A resource not supported by this repository. "
                    "Add a new resource handler to UserRepo.resource_handlers"
                )
            self.resource_handlers[res_type].save(res, repo_path=dest, **kwargs)
        logger.info(f"Repo.save: Saved {len(self.resources)} resources to {dest} repository")
