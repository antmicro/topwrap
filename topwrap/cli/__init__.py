# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
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
from topwrap import __version__
from topwrap.backend.yaml.common.ip_core_schema import IPCoreDescription
from topwrap.frontend.yaml.design import DesignDescriptionFrontendException
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.library import interface_definitions, module_index
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier
from topwrap.model.module import Module
from topwrap.repo.user_repo import Core, InterfaceDefinitionResource
from topwrap.resource_field import FileReferenceHandler
from topwrap.util import MarshmallowErrorRewriter, get_config, parse_incdirs, warn_deprecated

logger = logging.getLogger(__name__)

cli = cyclopts.App(
    default_parameter=cyclopts.Parameter(short_alias=True),
    help_format="restructuredtext",
    version=__version__,
)

repo_cli = cyclopts.App(name="repo", help="Commands related to user repositories", show=False)
cli.command(repo_cli)
library_cli = cyclopts.App(name="library", help="Commands related to libraries (based on FuseSoC)")
cli.command(library_cli)


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
    log_level: Annotated[Optional[LOG_LEVEL], Parameter(alias="-l")] = None,
    log_cfg: Annotated[Optional[ExistingFile], Parameter(alias="-L")] = None,
    repo: Annotated[Tuple[RepoDirectory, ...], Parameter(alias="-r", negative="--empty-repo")] = (),
):
    """Topwrap helps designers to manage and integrate IP cores into their SoC designs.

    Parameters
    ----------
    log_level : Optional[LOG_LEVEL]
        The logging level to set for the application.
    log_cfg : Optional[ExistingFile]
        Path to a logging configuration file.
    repo : Tuple[RepoDirectory, ...]
        A tuple of repository directories to include in the configuration.
        .. deprecated:: 1.0.0
    """
    err_rewriter = MarshmallowErrorRewriter()
    levelname = log_level.name if log_level else LOG_LEVEL.INFO.name
    topwrap.logger.configure(levelname, log_cfg)

    processed_tokens = list(tokens)

    if repo:
        warn_deprecated(
            "the '--repo' flag and user repositories are deprecated; register a "
            "topwrap library ('topwrap library add') and use 'core:' in the design"
        )
    for rep in repo:
        get_config().update_repo({rep.name: FileReferenceHandler(rep)})

    try:
        if processed_tokens == ["library", "add"]:
            cli.help_print(processed_tokens)
            sys.exit(1)

        # 'repo parse' is deprecated and only understands '+incdir+' via this
        # special-cased rewrite into '--include'. Every other command (e.g.
        # 'package') receives its raw tokens untouched and is responsible for
        # parsing any '+incdir+'/'+define+'-style arguments itself.
        PARSE_COMMAND = ["repo", "parse"]
        if processed_tokens[:2] == PARSE_COMMAND:
            include_dirs = parse_incdirs(tokens)
            cli_args = [t for t in processed_tokens if not t.startswith("+incdir+")]
            for inc in include_dirs:
                cli_args.extend(["--include", inc])
            return cli(cli_args)
        return cli(processed_tokens)
    except DesignDescriptionFrontendException as err:
        while err is not None:
            logger.error(err)
            err = err.__cause__
        sys.exit(1)
    except marshmallow.ValidationError as err:
        err_rewriter.parse(err.messages)
        for e in err_rewriter.messages:
            logger.error(e)

        sys.exit(1)

    except Exception as err:
        logger.error(err)
        sys.exit(1)


def load_modules_from_repos() -> tuple[Iterable[Module], set[Identifier]]:
    """Load all IR Modules from repositories and libraries in the config"""

    modules = list[Module]()
    existing_ifaces = set[Identifier]()
    failed = False
    for repo in get_config().loaded_repos.values():
        for core in repo.get_resources(Core):
            try:
                modules.append(core.top)
                existing_ifaces.update(core.existing_ifaces_ids)
            except Exception as e:
                logger.error(f"Could not load core '{core.name}' from repo '{repo.name}': {e}")
                failed = True

    for vlnv, path in module_index().items():
        try:
            desc = IPCoreDescription.load(path)
            modules.append(IPCoreDescriptionFrontend().parse(path, desc))
            existing_ifaces.update(desc.existing_iface_definitions)
        except Exception as e:
            logger.error(f"Could not load module '{vlnv}' from a library ({path}): {e}")
            failed = True

    # Report every unloadable core before quitting, so that a single broken
    # core doesn't hide the remaining ones
    if failed:
        sys.exit(1)

    return (modules, existing_ifaces)


def load_interfaces_from_repos() -> Iterator[InterfaceDefinition]:
    seen: set[Identifier] = set()
    for repo in get_config().loaded_repos.values():
        for intf in repo.get_resources(InterfaceDefinitionResource):
            if intf.definition.id not in seen:
                seen.add(intf.definition.id)
                yield intf.definition
    for intf in interface_definitions():
        if intf.id not in seen:
            seen.add(intf.id)
            yield intf


import topwrap.cli.library  # noqa: E402, F401
import topwrap.cli.package  # noqa: E402, F401
import topwrap.cli.repo  # noqa: E402, F401
