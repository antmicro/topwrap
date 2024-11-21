# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from functools import cached_property
import os
from pathlib import Path
from typing import List, Optional

import marshmallow
import marshmallow_dataclass
import yaml

from topwrap.common_serdes import MarshmallowDataclassExtensions, ext_field
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
class RepositoryEntry:
    """Contains information about topwrap repository"""

    name: str
    path: str

    @cached_property
    def repo(self) -> UserRepo:
        repo = UserRepo()
        repo.load(Path(self.path))
        return repo


@marshmallow_dataclass.dataclass
class Config(MarshmallowDataclassExtensions):
    """Global topwrap configuration"""

    force_interface_compliance: Optional[bool] = ext_field(False)
    repositories: Optional[List[RepositoryEntry]] = ext_field(list)
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
                for repo in config.repositories:
                    if repo not in self.repositories:
                        self.repositories.append(repo)

    def get_repositories_paths(self) -> List[Path]:
        repositories_paths = []
        if self.repositories is None:
            return repositories_paths
        for repository in self.repositories:
            repositories_paths.append(Path(repository.path).expanduser())
        return repositories_paths

    def get_repo_path_by_name(self, name: str) -> Optional[Path]:
        if self.repositories is None:
            return None
        for repo in self.repositories:
            if repo.name == name:
                return Path(repo.path)

    def get_builtin_repo(self) -> RepositoryEntry:
        return next(r for r in self.repositories if r.name == ConfigManager.BUILTIN_REPO_NAME)


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

    DEFAULT_SEARCH_PATHS = [
        "topwrap.yaml",
        "~/.config/topwrap/topwrap.yaml",
        "~/.config/topwrap/config.yaml",
    ]

    _interfaces_dir = Path("interfaces")

    def __init__(self, search_paths: Optional[List[str]] = None):
        if search_paths is None:
            search_paths = self.DEFAULT_SEARCH_PATHS

        self.search_paths = []
        for path in search_paths:
            self.search_paths += [Path(path).expanduser()]

    def load(self, overrides: Optional[Config] = None, default: Optional[Config] = None):
        config = Config() if default is None else default

        for path in reversed(self.search_paths):
            if not path.is_file():
                continue

            with open(path) as f:
                try:
                    yaml_dict = yaml.safe_load(f)
                except yaml.YAMLError:
                    logger.warning(f"{path} configuration file is not a valid YAML")
                    continue

            try:
                new_config = Config.from_dict(yaml_dict)
                config.update(new_config)
            except marshmallow.ValidationError as e:
                logger.warning(f"{path} configuration file is not valid ({e.messages})")
                continue

        if overrides is not None:
            config.update(overrides)

        logger.debug(f"Final configuration used by topwrap: {config}")

        return config


config = ConfigManager().load()
