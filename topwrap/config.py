# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import field
from os import PathLike
from pathlib import Path
from typing import List, Optional

import marshmallow
import marshmallow_dataclass
import yaml

from topwrap.repo.user_repo import UserRepo

logger = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    """Raised when the provided configuration is incorrect"""


@marshmallow_dataclass.dataclass
class RepositoryEntry:
    """Contains information about topwrap repository"""

    name: str
    path: str


@marshmallow_dataclass.dataclass
class Config:
    """Global topwrap configuration"""

    force_interface_compliance: Optional[bool] = field(
        default=False, metadata={"load_default": None}
    )
    repositories: Optional[List[RepositoryEntry]] = field(
        default_factory=list, metadata={"load_default": None}
    )

    def update(self, config: "Config"):
        if config.force_interface_compliance is not None:
            self.force_interface_compliance = config.force_interface_compliance

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

    def get_interface_paths(self) -> List[Path]:
        interfaces_paths: List[Path] = list()
        if self.repositories is None:
            return interfaces_paths
        for repository in self.repositories:
            interface_path = UserRepo.get_interfaces_directory(Path(repository.path).expanduser())
            if interface_path is not None:
                interfaces_paths.append(interface_path)
        return interfaces_paths


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

    def __init__(self, search_paths: Optional[List[PathLike]] = None):
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
                new_config = Config.Schema().load(yaml_dict)
                config.update(new_config)
            except marshmallow.ValidationError as e:
                logger.warning(f"{path} configuration file is not valid ({e.messages})")
                continue

        if overrides is not None:
            config.update(overrides)

        logger.debug(f"Final configuration used by topwrap: {config}")

        return config


config = ConfigManager().load()
