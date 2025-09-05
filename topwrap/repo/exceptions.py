# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from topwrap.repo.repo import Repo
    from topwrap.repo.resource import Resource
    from topwrap.repo.user_repo import Core


class ResourceNotSupportedException(Exception):
    """
    Raised when a resource is not supported

    If you are developer and want to add support for resource you need to add resource handler
    check UserRepo how it is done
    """

    resource: Type["Resource"]
    repo: Type["Repo"]

    def __init__(self, resource: Type["Resource"], repo: Type["Repo"], *args: object) -> None:
        self.resource = resource
        self.repo = repo
        super().__init__(
            f'Resource type "{self.resource.__name__}" is not supported by repository'
            + f' of type "{self.repo.__name__}"',
            *args,
        )


class ResourceExistsException(Exception):
    """Raised when resource already exist"""

    resource: "Resource"
    repo: Optional["Repo"]

    def __init__(self, resource: "Resource", repo: Optional["Repo"] = None, *args: object) -> None:
        self.resource = resource
        self.repo = repo
        super().__init__(
            f'Resource "{resource.name}" already exists'
            + (f' in repository "{self.repo.name}"' if self.repo is not None else ""),
            *args,
        )


class ResourceNotFoundException(Exception):
    """Raised when resource doesn't exist"""

    resource: str
    repo_name: Optional[str]

    def __init__(self, resource: str, repo_name: Optional[str] = None, *args: object) -> None:
        self.resource = resource
        self.repo_name = repo_name
        super().__init__(
            f'Resource "{resource}" could not be found in repository "{self.repo_name or ""}"',
            *args,
        )


class TopLevelNotFoundException(Exception):
    core: Core

    def __init__(self, core: Core, *args: object) -> None:
        self.core = core

        super().__init__(
            f"Could not find the top level module '{core.top_level_name}'"
            f" in the sources of '{core.name}' core",
            *args,
        )
