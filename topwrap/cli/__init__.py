# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Iterable, Iterator, Optional, Sequence, Tuple

import cyclopts
import marshmallow
from cyclopts import Parameter
from cyclopts.types import ExistingDirectory, ExistingFile

import topwrap.logger
from topwrap.config import config
from topwrap.frontend.yaml.design import DesignDescriptionFrontendException
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module
from topwrap.repo.user_repo import Core, InterfaceDefinitionResource
from topwrap.resource_field import FileReferenceHandler
from topwrap.util import get_config

logger = logging.getLogger(__name__)

cli = cyclopts.App(default_parameter=cyclopts.Parameter(short_alias=True))
repo_cli = cyclopts.App(name="repo", help="Commands related to user repositories")
cli.command(repo_cli)


class LOG_LEVEL(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _resolve_repo_directory(type_, tokens: Sequence) -> Path:
    assert len(tokens) == 1
    value = tokens[0].value
    if (repo_path_cfg := get_config().repositories.get(value)) is not None:
        return repo_path_cfg.to_path()
    return Path(value)


RepoDirectory = Annotated[ExistingDirectory, Parameter(converter=_resolve_repo_directory)]


@cli.meta.default
def cmd(
    *tokens: Annotated[str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)],
    log_level: Optional[LOG_LEVEL] = None,
    log_cfg: Optional[ExistingFile] = None,
    repo: Tuple[RepoDirectory, ...] = (),
):
    levelname = None if log_level is None else log_level.name
    topwrap.logger.configure(levelname, log_cfg)

    for rep in repo:
        config.repositories[rep.name] = FileReferenceHandler(rep)

    try:
        return cli(tokens)
    except DesignDescriptionFrontendException as err:
        while err is not None:
            logger.error(err)
            err = err.__cause__
        sys.exit(1)
    except marshmallow.ValidationError as err:
        for fieldname, message in err.messages:
            logger.error("Failed to parse {} field. {}".format(fieldname, message))
        sys.exit(1)
    except Exception as err:
        logger.error(err)
        sys.exit(1)


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


import topwrap.cli.repo  # noqa: E402, F401
