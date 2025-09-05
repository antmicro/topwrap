# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import List, cast

import click

from topwrap.config import ConfigManager, config
from topwrap.frontend.automatic import AutomaticFrontend, FrontendRegistry
from topwrap.repo.exceptions import ResourceNotSupportedException
from topwrap.repo.file_handlers import CoreFileHandler
from topwrap.repo.files import File, LocalFile
from topwrap.repo.repo import (
    ExistsStrategy,
)
from topwrap.repo.resource import ResourceExistsException
from topwrap.repo.user_repo import Core, UserRepo
from topwrap.resource_field import FileReferenceHandler
from topwrap.util import get_config

logger = logging.getLogger(__name__)


@click.group(help="Commands related to user repositories")
def repo():
    pass


@repo.command(
    help="Parse Modules from all provided files using available frontends"
    " and store them in a given user repository. The repository can be selected"
    " by its name from config or a path to a directory, even when it's not"
    " included in the config `repositories` key.",
    name="parse",
)
@click.option(
    "--all-sources",
    "-a",
    is_flag=True,
    help="Instead of automatically trying to detect the minimal fileset required for a Module"
    " among the supplied sources generously pack all of them into the repo",
)
@click.option(
    "--module",
    "-m",
    multiple=True,
    help="Only store the module with this name instead of all provided",
)
@click.option(
    "--reference",
    "-l",
    is_flag=True,
    help="Instead of copying all required sources to the repository, just reference their current"
    " location",
)
@click.option(
    "--exists-strategy",
    "-e",
    type=click.Choice(list(ExistsStrategy), False),
    default=ExistsStrategy.RAISE,
    show_default=True,
    help="How to behave in case a Module already exists in the repository",
)
@click.option(
    "--frontend",
    "-f",
    type=click.Choice(list(FrontendRegistry.BY_NAME), False),
    default=AutomaticFrontend().metadata.name,
    show_default=True,
    help="Which frontend should be used for these sources",
)
@click.argument("repository")
@click.argument(
    "sources",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, path_type=Path),
)
def parse_repo(
    exists_strategy: ExistsStrategy,
    all_sources: bool,
    sources: tuple[Path, ...],
    repository: str,
    module: tuple[str, ...],
    reference: bool,
    frontend: str,
):
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
    try:
        cores = CoreFileHandler(
            file_srcs, FrontendRegistry.BY_NAME[frontend](), module, all_sources
        ).parse()
        for core in cores:
            if reference:
                cast(Core, core).by_ref = True
            repo.add_resource(core, exists_strategy)
        repo.save(repo_path.to_path())
    except (
        ResourceExistsException,
        ResourceNotSupportedException,
    ) as e:
        logging.error(e)


@repo.command(help="List all repos in current config", name="list")
def list_repos():
    print("Loaded user repositories:")
    for name, path in config.repositories.items():
        print(f'"{name}" -> "{path.to_path()}"')


@repo.command(help="Create new repo", name="init")
@click.argument("name")
@click.argument(
    "path",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
)
def init_repo(name: str, path: Path):
    path.mkdir(exist_ok=True, parents=True)
    if next(path.iterdir(), None) is not None:
        logging.error(f"The directory selected for the new repository ('{path}') is not empty")
        return
    repo = UserRepo(name)
    repo.save(path)
    config.repositories[name] = FileReferenceHandler(path)
    logging.info(f"Created a new repository named '{name}' in '{path}'")
