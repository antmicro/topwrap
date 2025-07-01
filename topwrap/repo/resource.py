# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, List, Type, TypeVar


class Resource(ABC):  # noqa: B024
    """Base class for representing a resource in a repository"""


ResourceType = TypeVar("ResourceType", bound=Resource)


class ResourceHandler(Generic[ResourceType], ABC):
    """Base for classes that can perform various operations on resources"""

    resource_type: Type[ResourceType]

    @abstractmethod
    def save(self, res: ResourceType, repo_path: Path) -> None:
        """Saves a resource in the repo_path repository"""

    @abstractmethod
    def load(self, repo_path: Path) -> List[ResourceType]:
        """Loads list of resources from the repo_path repository"""


class FileHandler(ABC):
    @abstractmethod
    def parse(self) -> List[Resource]:
        """Parses a file to extract resources"""
