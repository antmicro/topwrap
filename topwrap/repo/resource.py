# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Iterable, Iterator, List, Type, TypeVar

from topwrap.repo.exceptions import ResourceExistsException, ResourceNotFoundException
from topwrap.repo.files import File
from topwrap.util import ExistsStrategy


class Resource(ABC):  # noqa: B024
    """
    Base class for representing a resource in a repository.
    Each derived resource should define its own structure.
    """

    #: Name of the resource
    name: str

    def __init__(self, name: str):
        self.name = name


ResourceType = TypeVar("ResourceType", bound=Resource)


class ResourceHandler(Generic[ResourceType], ABC):
    """
    Base for classes that can perform various operations on resources of a given type.

    The main responsibilities of a resource handler are saving and loading resources
    of a given type in a repository.
    """

    #: For which resource type this handler is responsible
    resource_type: Type[ResourceType]

    @abstractmethod
    def save(self, res: ResourceType, repo_path: Path) -> None:
        """Saves a resource in the repo_path repository"""

    @abstractmethod
    def load(self, repo_path: Path) -> Iterator[ResourceType]:
        """Loads list of resources from the repo_path repository"""

    def add_resource(
        self,
        resources: dict[str, ResourceType],
        res: ResourceType,
        exists_strategy: ExistsStrategy = ExistsStrategy.RAISE,
    ):
        """
        Custom behavior for adding a resource to a loaded repository
        :raises ResourceExistsException: Resource already exists in the repository
        """
        if res.name in resources:
            if exists_strategy is ExistsStrategy.RAISE:
                raise ResourceExistsException(res)
            elif exists_strategy is ExistsStrategy.SKIP:
                return
            elif exists_strategy is ExistsStrategy.OVERWRITE:
                self.remove_resource(resources, resources[res.name])
        resources[res.name] = res

    def remove_resource(self, resources: dict[str, ResourceType], res: ResourceType):
        """
        Custom behavior for removing a resource from a loaded repository
        :raises ResourceNotFoundException: Could not find that resource
        """
        if res.name not in resources:
            raise ResourceNotFoundException(res.name)
        resources.pop(res.name, None)


class FileHandler(ABC):
    """
    Base class for file handlers.
    A file handler is used to extract repository resources
    from a set of given files.
    """

    _files: list[File]

    def __init__(self, files: Iterable[File]):
        self._files = list(files)

    @abstractmethod
    def parse(self) -> List[Resource]:
        """Parses a file to extract resources"""
