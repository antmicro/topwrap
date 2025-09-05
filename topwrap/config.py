# Copyright (c) 2021-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from functools import cached_property
from pathlib import Path
from typing import Optional, Sequence

import marshmallow
import marshmallow_dataclass
import yaml
from importlib_resources import as_file, files

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    ResourcePathT,
    ext_field,
)
from topwrap.repo.user_repo import UserRepo

logger = logging.getLogger(__name__)

DEFAULT_SERVER_BASE_DIR = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.local/cache")).expanduser() / "topwrap/kpm_build"
)
DEFAULT_WORKSPACE_DIR = "workspace"
DEFAULT_BACKEND_DIR = "backend"
DEFAULT_FRONTEND_DIR = "frontend"
DEFAULT_SERVER_ADDR = "127.0.0.1"
DEFAULT_SERVER_PORT = 9000
DEFAULT_BACKEND_ADDR = "127.0.0.1"
DEFAULT_BACKEND_PORT = 5000


class InvalidConfigError(Exception):
    """Raised when the provided configuration is incorrect"""


@marshmallow_dataclass.dataclass
class Config(MarshmallowDataclassExtensions):
    """Global topwrap configuration"""

    force_interface_compliance: Optional[bool] = ext_field(False)
    repositories: dict[str, ResourcePathT] = ext_field(dict)
    kpm_build_location: str = ext_field(str(DEFAULT_SERVER_BASE_DIR))

    def update(self, config: "Config"):
        if config.force_interface_compliance is not None:
            self.force_interface_compliance = config.force_interface_compliance

        if config.kpm_build_location is not None:
            self.kpm_build_location = config.kpm_build_location

        if config.repositories is not None:
            if self.repositories is None:
                self.repositories = config.repositories
            else:
                self.repositories.update(config.repositories)

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

    BUILTIN_DIR = as_file(files(f"topwrap.{BUILTIN_REPO_NAME}"))

    DEFAULT_SEARCH_PATHS = [
        Path("topwrap.yaml"),
        Path("~/.config/topwrap/topwrap.yaml"),
        Path("~/.config/topwrap/config.yaml"),
        BUILTIN_DIR.__enter__() / "default_config.yaml",
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
                config.update(new_config)
            except (marshmallow.ValidationError, yaml.YAMLError) as e:
                logger.warning(f"{path} configuration file is not valid ({e})")
                continue

        if overrides is not None:
            config.update(overrides)

        logger.debug(f"Final configuration used by topwrap: {config}")

        return config


config = ConfigManager().load()
