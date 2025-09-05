# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Any, Iterator, Optional

import click

from topwrap.frontend.yaml.ip_core import InterfaceDescriptionFrontend
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module
from topwrap.repo.user_repo import Core, InterfaceDescription
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


def load_modules_from_repos() -> Iterator[Module]:
    """Load all IR Modules from repositories in the config"""

    for repo in get_config().loaded_repos.values():
        for core in repo.get_resources(Core):
            try:
                loaded_core = core.ir_module
                for unknown_source in loaded_core.unknown_sources:
                    logger.warning(
                        f"Could not find a matching frontend for source '{unknown_source}' "
                        f"of core '{core.name}' in repo '{repo.name}'"
                    )
                yield loaded_core.top_level
            except Exception as e:
                logger.error(f"Could not load core '{core.name}' from repo '{repo.name}': {e}")


def load_interfaces_from_repos() -> Iterator[InterfaceDefinition]:
    for repo in get_config().loaded_repos.values():
        for intf in repo.get_resources(InterfaceDescription):
            yield InterfaceDescriptionFrontend().parse(intf.file.path)
