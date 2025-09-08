# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Type, cast

from topwrap.repo.exceptions import (
    ResourceNotFoundException,
    ResourceNotSupportedException,
)
from topwrap.repo.resource import (
    FileHandler,
    Resource,
    ResourceHandler,
    ResourceType,
)
from topwrap.util import ExistsStrategy

logger = logging.getLogger(__name__)

ParseHandler = Callable[..., List[Resource]]
RepoParseHandlers = Dict[Enum, ParseHandler]
RepoResourceHandlers = Dict[ResourceType, ResourceHandler[ResourceType]]


class Repo(ABC):
    """
    Base class for implementing repositories.
    A repository is a container for resources of various types.

    Derived classes should be associated with a set of supported
    resource handlers that define what types of resources can
    be stored in the repo. An example of such derived repo is
    :class:`~topwrap.repo.user_repo.UserRepo`
    """

    #: Name of the repository
    name: str

    def __init__(self, resource_handlers: List[ResourceHandler[Resource]], name: str) -> None:
        """
        Initialize the repository.

        :param resource_handlers: A list of handlers that define which resources are
            supported in this repository and how are they handled
        """
        self.name = name
        self.resources: Dict[Type[Resource], Dict[str, Resource]] = {}
        self.resource_handlers: dict[Type[Resource], ResourceHandler[Resource]] = {}
        for handler in resource_handlers:
            self.resources[handler.resource_type] = {}
            self.resource_handlers[handler.resource_type] = handler

    @property
    def n_resources(self):
        return sum(len(rs) for rs in self.resources.values())

    def add_files(
        self, handler: FileHandler, exist_strategy: ExistsStrategy = ExistsStrategy.RAISE
    ) -> None:
        """
        Parses resources available in files and adds them to the repository

        :param handler: Handler that contains sources
        :param exist_strategy: What to do if resource exists in repo already

        :raise ResourceExistsException: Raised when exist_strategy is set to RAISE
        :raise ResourceNotSupportedException:
            Raised when handler returns resources not supported by repo
        """
        resources = handler.parse()
        logger.info(f"Repo.add_file: Obtained {len(resources)} resources from {handler}")
        for resource in resources:
            self.add_resource(resource, exist_strategy)

    def add_resource(
        self, resource: Resource, exist_strategy: ExistsStrategy = ExistsStrategy.RAISE
    ) -> None:
        """
        Adds a single resource to the repository

        :param resource: Resource to add to repo
        :param exist_strategy: What to do if resource exists

        :raise: ResourceExistsException: Raised if exist_strategy is set to RAISE
        :raise: ResourceNotSupportedException: Raised if the repository doesn't have a
            handler for this resource type
        """

        if type(resource) not in self.resource_handlers:
            raise ResourceNotSupportedException(type(resource), type(self))
        handler = self.resource_handlers[type(resource)]
        handler.add_resource(self.resources[type(resource)], resource, exist_strategy)

    def remove_resource(self, resource: Resource) -> None:
        """
        Removes a single resource from repository

        :param resource: Resource to remove from repo

        :raise ResourceNotFoundException: Raised when resource is not present in repository
        :raise ResourceNotSupportedException: Raised if repo don't have handler for
            this resource type
        """
        if type(resource) not in self.resource_handlers:
            raise ResourceNotSupportedException(type(resource), type(self))
        try:
            self.resource_handlers[type(resource)].remove_resource(
                self.resources[type(resource)], resource
            )
        except ResourceNotFoundException as e:
            e.repo_name = self.name
            raise e

    def get_resource(self, resource_type: type[ResourceType], name: str) -> ResourceType:
        """
        Searches for resource with given type in repository

        :raise ResourceNotFoundException: Raised when resource with given name isn't present
        :raise ResourceNotSupportedException: Raised when resource is not supported by repo
            implementation
        """
        if resource_type not in self.resources:
            raise ResourceNotSupportedException(resource_type, type(self))
        if name not in self.resources[resource_type]:
            exception = ResourceNotFoundException(name)
            exception.repo_name = self.name
            raise exception
        return cast(ResourceType, self.resources[resource_type][name])

    def get_resources(self, type: Type[ResourceType]) -> List[ResourceType]:
        """Implements the same operation as self.resources[type] but gives correct hints to the
        typechecker"""
        return cast(List[ResourceType], self.resources[type].values())

    def load(self, repo_path: Path, **kwargs: Any) -> None:
        """Loads repository from repo_path"""
        for handler in self.resource_handlers.values():
            resources = handler.load(Path(repo_path).expanduser())
            for resource in resources:
                self.add_resource(resource)

        logger.info(f"Repo.load: Loaded {self.n_resources} resources from {repo_path}")

    def save(self, dest: Path, **kwargs: Any) -> None:
        """
        Saves repository to dest
        :raises ResourceNotSupportedException:
        """
        for res_type_value in self.resources.values():
            for res in res_type_value.values():
                if type(res) not in self.resource_handlers:
                    raise ResourceNotSupportedException(type(res), type(self))
                self.resource_handlers[type(res)].save(res, dest, **kwargs)

        logger.info(f"Repo.save: Saved {self.n_resources} resources to {dest} repository")
