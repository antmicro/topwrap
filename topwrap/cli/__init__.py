# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

import click

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module
from topwrap.repo.user_repo import Core, InterfaceDefinitionResource
from topwrap.util import get_config

logger = logging.getLogger(__name__)


class RepositoryPathParam(click.Path):
    """
    Handler for the repository CLI argument. Supports both a path
    to the repository or a name of the repository.
    """

    def convert(self, value: Any, param: Optional[Any], ctx: Optional[Any]) -> Path:
        if (
            isinstance(value, str)
            and (repo_path_cfg := get_config().repositories.get(value)) is not None
        ):
            return repo_path_cfg.to_path()
        else:
            return super().convert(value, param, ctx)


def load_modules_from_repos() -> tuple[Iterable[Module], list[InterfaceDefinition]]:
    """Load all IR Modules from repositories in the config"""

    modules = list[Module]()
    existing_ifaces = list[InterfaceDefinition]()
    for repo in get_config().loaded_repos.values():
        for core in repo.get_resources(Core):
            try:
                modules.append(core.top)
                existing_ifaces.extend(core.existing_ifaces)
            except Exception as e:
                logger.error(f"Could not load core '{core.name}' from repo '{repo.name}': {e}")
    return (modules, existing_ifaces)


def load_interfaces_from_repos() -> Iterator[InterfaceDefinition]:
    for repo in get_config().loaded_repos.values():
        for intf in repo.get_resources(InterfaceDefinitionResource):
            yield intf.definition
