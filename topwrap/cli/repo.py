# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import List, Tuple

import yaml
from cyclopts.types import ExistingPath

from topwrap.cli import load_interfaces_from_repos, load_modules_from_repos, repo_cli
from topwrap.config import ConfigManager
from topwrap.frontend.automatic import FrontendRegistry
from topwrap.repo.exceptions import ResourceNotSupportedException
from topwrap.repo.file_handlers import ModuleFileHandler
from topwrap.repo.files import File, LocalFile
from topwrap.repo.repo import (
    ExistsStrategy,
)
from topwrap.repo.resource import ResourceExistsException
from topwrap.repo.user_repo import UserRepo
from topwrap.resource_field import FileReferenceHandler
from topwrap.util import get_config

logger = logging.getLogger(__name__)


@repo_cli.command(name="parse")
def parse_repo(
    repository: str,
    sources: Tuple[ExistingPath, ...],
    *,
    exists_strategy: ExistsStrategy = ExistsStrategy.RAISE,
    all_sources: bool = False,
    module: Tuple[str, ...] = (),
    frontend: FrontendRegistry.FrontendType = FrontendRegistry.FrontendType.Automatic,
    inference: bool = False,
    inference_interface: Tuple[str, ...] = (),
    grouping_hint: Tuple[str, ...] = (),
):
    """Parse Modules from all provided files using available frontends and store
    them in a given user repository.

    Parameters
    ----------
    repository
        Repository name from config.
    sources
        Files to parse.
    exists_strategy
        How to behave when a Module already exists in the repository.
    all_sources
        Pack all supplied sources into each Module instead of detecting the
        minimal required fileset.
    module
        Only store modules with these names (repeatable).
    frontend
        Which frontend to use for these sources.
    inference
        Perform interface inference on modules being added.
    inference_interface
        Candidate interfaces for inference (repeatable).
    grouping_hint
        Grouping hints for interface inference.
    """
    repo_path = get_config().repositories.get(repository)

    if repo_path is None:
        logger.error(
            "Could not find repository '%s'. Make sure it's included in a configuration file.",
            repository,
        )
        exit(1)

    repo = UserRepo(repository)
    repo.load(repo_path.to_path())

    srcs = list(sources)

    for src in srcs[:]:
        if src.is_dir():
            srcs.extend(src.glob("**/*"))

    file_srcs: List[File] = [LocalFile(s) for s in srcs if not s.is_dir()]

    repo_modules, repo_ifaces = load_modules_from_repos()
    repo_ifaces.extend(load_interfaces_from_repos())

    try:
        resources = ModuleFileHandler(
            file_srcs,
            FrontendRegistry.BY_NAME[frontend](modules=repo_modules, interfaces=repo_ifaces),
            module,
            all_sources,
            inference,
            inference_interface,
            grouping_hint,
        ).parse()
        for res in resources:
            repo.add_resource(res, exists_strategy)
        repo.save(repo_path.to_path())
    except (
        ResourceExistsException,
        ResourceNotSupportedException,
    ) as e:
        logging.error(e)
    except OSError as e:
        logger.warning(
            "Path {} exceeding the limit. Contents of the file won't be used.".format(e.filename)
        )


@repo_cli.command(name="list")
def list_repos():
    """List all repos in current config"""

    print("Loaded user repositories:")
    for name, path in get_config().repositories.items():
        print(f'"{name}" -> "{path.to_path()}"')


@repo_cli.command(name="init")
def init_repo(
    name: str,
    path: Path,
    *,
    config_update: bool = True,
):
    """Create new repo"""

    path.mkdir(exist_ok=True, parents=True)
    if next(path.iterdir(), None) is not None:
        logging.error(f"The directory selected for the new repository ('{path}') is not empty")
        return
    repo = UserRepo(name)
    repo.save(path)
    get_config().repositories[name] = FileReferenceHandler(path)

    # TODO: Use the config updating mechanism when its added
    # instead of doing this manually
    local_cfg: Path = ConfigManager.DEFAULT_SEARCH_PATHS[0]
    repo_cfg = yaml.safe_load(local_cfg.open()) if local_cfg.exists() else {}
    if config_update:
        repo_cfg.setdefault("repositories", {})[name] = FileReferenceHandler(path).to_str()
        yaml.safe_dump(repo_cfg, local_cfg.open("w"))

    logging.info(f"Created a new repository named '{name}' in '{path}'")
