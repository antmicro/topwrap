# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import Iterator, Optional, Sequence

import marshmallow
import marshmallow_dataclass
import yaml

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    ResourcePathT,
    ext_field,
)
from topwrap.repo.user_repo import UserRepo

logger = logging.getLogger(__name__)


@marshmallow_dataclass.dataclass
class Config(MarshmallowDataclassExtensions):
    """Global topwrap configuration"""

    force_interface_compliance: Optional[bool] = ext_field(False)
    repositories: dict[str, ResourcePathT] = ext_field(dict)
    libraries: dict[str, str] = ext_field(dict)

    def update_repo(self, repos: dict[str, ResourcePathT]):
        self.repositories.update(repos)
        self._clear_cached_repo()

    def update_interface_compliance(self, force_interface_compliance: Optional[bool]):
        self.force_interface_compliance = force_interface_compliance

    def update_libraries(self, libraries: dict[str, str]):
        if not libraries:
            return
        self.libraries.update(libraries)
        from topwrap.library import clear_index_cache

        clear_index_cache()

    def update(self, config: "Config"):
        if config.force_interface_compliance is not None:
            self.update_interface_compliance(config.force_interface_compliance)

        if config.repositories is not None:
            self.update_repo(config.repositories)

        if config.libraries is not None:
            self.update_libraries(config.libraries)

    def _clear_cached_repo(self):
        self.__dict__.pop("loaded_repos", None)
        self.__dict__.pop("builtin_repo", None)

    @cached_property
    def loaded_repos(self) -> dict[str, UserRepo]:
        repos = {}
        for name, path in self.repositories.items():
            repo = UserRepo(name)
            repo.load(path.to_path())
            repos[name] = repo
        return repos

    @cached_property
    def builtin_repo(self) -> UserRepo:
        repo = UserRepo(ConfigManager.BUILTIN_REPO_NAME)
        repo.load(self.repositories[ConfigManager.BUILTIN_REPO_NAME].to_path())
        return repo


def _resolve_library_uris(libraries: dict[str, str], base: Path) -> dict[str, str]:
    """Resolve relative local-path library URIs against ``base``.

    A URI that carries a scheme (``https://``, ...) is left untouched. One that
    points at an existing directory relative to ``base`` (the directory of the
    config file it was declared in) is made absolute, so e.g. the builtin
    ``libraries: {builtin: .}`` resolves to the installed ``topwrap/builtin``
    directory regardless of the working directory. Remote URIs that carry no
    scheme (``git@host:repo``) are left alone by virtue of not naming a
    directory.
    """
    resolved: dict[str, str] = {}
    for name, uri in libraries.items():
        candidate = (base / uri).expanduser()
        if "://" not in uri and candidate.is_dir():
            resolved[name] = str(candidate.resolve())
        else:
            resolved[name] = uri
    return resolved


_BUILTIN_CONFIG_NAME = "default_config.yaml"


class InvalidConfigError(Exception):
    """Raised when the provided configuration is incorrect"""


class ConfigManager:
    """Manager used to load topwrap's configuration from files.

    The configuration files are loaded in a specific order, which also
    determines the priority of settings that are defined differently
    in the files. The list of default search paths is defined in
    the `DEFAULT_SEARCH_PATH` class variable. Configuration files that
    are specified earlier in the list have higher priority and can
    overwrite the settings from the files that follow. The default list of
    search paths can be changed by passing a different list to
    the ConfigManager constructor.
    """

    BUILTIN_REPO_NAME = "builtin"

    BUILTIN_DIR = Path(__file__).parent / BUILTIN_REPO_NAME

    DEFAULT_SEARCH_PATHS = [
        Path("topwrap.yaml"),
        Path("~/.config/topwrap/topwrap.yaml"),
        Path("~/.config/topwrap/config.yaml"),
        BUILTIN_DIR / _BUILTIN_CONFIG_NAME,
    ]

    def __init__(self, search_paths: Optional[Sequence[Path]] = None):
        if search_paths is None:
            search_paths = self.DEFAULT_SEARCH_PATHS

        self.search_paths: list[Path] = []
        for path in search_paths:
            self.search_paths.append(path.expanduser())

    def load(self, overrides: Optional[Config] = None, default: Optional[Config] = None):
        config = Config() if default is None else default

        for path in reversed(self.search_paths):
            if not path.is_file():
                continue

            try:
                new_config = Config.load(path)
                new_config.libraries = _resolve_library_uris(new_config.libraries, path.parent)
                config.update(new_config)
            except (marshmallow.ValidationError, yaml.YAMLError) as e:
                logger.warning(f"{path} configuration file is not valid ({e}), skipping")
                continue

        if overrides is not None:
            config.update(overrides)

        logger.debug(f"Final configuration used by topwrap: {config}")

        return config


config = ConfigManager().load()


@contextmanager
def library_scope(libraries: dict[str, str], *, replace: bool = False) -> Iterator[None]:
    """Temporarily add or replace configured libraries."""
    original = dict(config.libraries)
    effective = {} if replace else dict(original)
    effective.update(libraries)

    from topwrap.library import clear_index_cache

    config.libraries.clear()
    config.libraries.update(effective)
    clear_index_cache()
    try:
        yield
    finally:
        config.libraries.clear()
        config.libraries.update(original)
        clear_index_cache()
