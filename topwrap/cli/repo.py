# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Annotated, List, Tuple

import yaml
from cyclopts import Parameter
from cyclopts.types import ExistingDirectory, ExistingFile, ExistingPath

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
from topwrap.util import get_config, parse_params, warn_deprecated

logger = logging.getLogger(__name__)

_REPO_DEPRECATION = (
    "'topwrap repo' and the user-repository mechanism are deprecated and will be "
    "removed; use 'topwrap library' and reference cores with 'core:' in the design"
)


@repo_cli.command(name="parse")
def parse_repo(
    repository: Annotated[str, Parameter(alias="-r")],
    sources: Annotated[
        Tuple[ExistingPath, ...], Parameter(alias="-s", negative="--empty-sources")
    ] = (),
    *,
    exists_strategy: Annotated[ExistsStrategy, Parameter(alias="-e")] = ExistsStrategy.RAISE,
    all_sources: Annotated[bool, Parameter(alias="-a", negative="--no-all-sources")] = False,
    module: Annotated[Tuple[str, ...], Parameter(alias="-m", negative="--empty-module")] = (),
    file: Annotated[Tuple[ExistingFile, ...], Parameter(alias="-f", negative="--empty-file")] = (),
    include: Annotated[
        Tuple[ExistingDirectory, ...], Parameter(alias="-i", negative="--empty-include")
    ] = (),
    frontend: Annotated[
        FrontendRegistry.FrontendType, Parameter(alias="-F")
    ] = FrontendRegistry.FrontendType.Automatic,
    inference: Annotated[bool, Parameter(alias="-I", negative="--no-inference")] = False,
    inference_interface: Annotated[
        Tuple[str, ...], Parameter(negative="--empty-inference-interface")
    ] = (),
    grouping_hint: Annotated[
        Tuple[str, ...], Parameter(alias="-g", negative="--empty-grouping-hint")
    ] = (),
):
    """Parse Modules from all provided files using available frontends and store
    them in a given user repository.

    .. deprecated::
        See ``topwrap library``.

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
    file
        Specify filelist path
    include
        Specify directory containing included sources
    inference
        Perform interface inference on modules being added.
    inference_interface
        Candidate interfaces for inference (repeatable).
    grouping_hint
        Grouping hints for interface inference.
    """
    warn_deprecated(_REPO_DEPRECATION)
    repo_path = get_config().repositories.get(repository)

    if len(file) == 0:
        if len(sources) == 0:
            logger.error("Sources must be provided either as an argument or using -f parameter")
            exit(1)

    if repo_path is None:
        logger.error(
            "Could not find repository '%s'. Make sure it's included in a configuration file.",
            repository,
        )
        exit(1)

    repo = UserRepo(repository)
    repo.load(repo_path.to_path())

    srcs = list(sources)
    incdirs = list()

    incdirs.extend(include)

    if len(file) > 0:
        for f in file:
            load_srcs_from_file(srcs, incdirs, f)

    for src in srcs[:]:
        if src.is_dir():
            srcs.extend(src.glob("**/*"))

    file_srcs: List[File] = [LocalFile(s) for s in srcs if not s.is_dir()]

    repo_modules, _ = load_modules_from_repos()

    try:
        resources = ModuleFileHandler(
            file_srcs,
            FrontendRegistry.BY_NAME[frontend](
                modules=repo_modules, interfaces=load_interfaces_from_repos()
            ),
            module,
            all_sources,
            incdirs,
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
        exit(1)
    except OSError as e:
        logger.warning(
            "Path {} exceeding the limit. Contents of the file won't be used.".format(e.filename)
        )


def load_srcs_from_file(srcs: list[Path], incdirs: list[Path], file: Path) -> None:
    def is_comment(line: str) -> bool:
        return line.startswith("//")

    files = [file]

    while len(files) > 0:
        curr_file = files.pop()
        with open(curr_file) as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or is_comment(line):
                    continue
                if line.startswith("+incdir+"):
                    inc_strs: list[str] = parse_params("+incdir+", line)
                    for inc in inc_strs:
                        incdirs.append(Path(inc))
                    continue
                elif line.startswith("-F "):
                    files.append(curr_file.parent / Path(line.lstrip("-F ")))
                    continue
                path = Path(line)
                if not path.exists():
                    logger.warning("Path {} does not exist".format(line))
                    continue
                srcs.append(path)


@repo_cli.command(name="list", help="List all repos in current config")
def list_repos():
    """List all repos in current config"""
    warn_deprecated(_REPO_DEPRECATION)

    print("Loaded user repositories:")
    for name, path in get_config().repositories.items():
        print(f'"{name}" -> "{path.to_path()}"')


@repo_cli.command(name="init")
def init_repo(
    name: Annotated[str, Parameter(alias="-n")],
    path: Annotated[Path, Parameter(alias="-p")],
    *,
    config_update: Annotated[bool, Parameter(negative="--no-config-update")] = True,
):
    """Create new repo"""
    warn_deprecated(_REPO_DEPRECATION)

    path.mkdir(exist_ok=True, parents=True)
    if next(path.iterdir(), None) is not None:
        logging.error(f"The directory selected for the new repository ('{path}') is not empty")
        exit(1)
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
