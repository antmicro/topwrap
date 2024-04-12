# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

import pytest
import yaml

from topwrap.config import Config, ConfigManager, RepositoryEntry


class TestConfigManager:
    @pytest.fixture
    def config_dict(self):
        return Config.Schema().dump(
            Config(
                force_interface_compliance=True,
                repositories=[
                    RepositoryEntry("My topwrap repo", "~/custom/repo/path"),
                ],
            )
        )

    @pytest.fixture
    def custom_config_dicts(self):
        return [
            (
                "custom/path/cfg.yml",
                Config.Schema().dump(Config(repositories=[RepositoryEntry("repo1", "path1")])),
            ),
            (
                "/global/path/mycfg.yaml",
                Config.Schema().dump(Config(repositories=[RepositoryEntry("repo2", "path2")])),
            ),
        ]

    @pytest.fixture
    def incorrect_config_dicts(self):
        return [
            {
                "force_interface_compliance": True,
                "repositories": [
                    {
                        "name": "My topwrap repo",
                        "path": "~/custom/repo/path",
                        "info": "Info should not be here",
                    }
                ],
            },
            {
                "force_interface_compliance": True,
                "meta": "A missing 'repositories' entry is correct, an additional custom entry is not",
            },
        ]

    @staticmethod
    def contains_warnings_in_log(caplog):
        for name, level, msg in caplog.record_tuples:
            if name == "topwrap.config" and level == logging.WARNING:
                return True
        return False

    def test_adding_repo_duplicates(self, fs, config_dict, caplog):
        (repo_dict,) = config_dict["repositories"]

        manager = ConfigManager()
        for path in manager.search_paths:
            config_str = yaml.dump(config_dict)
            fs.create_file(path, contents=config_str)

        config = manager.load()
        assert len(config.repositories) == 1
        assert not self.contains_warnings_in_log(caplog)

    def test_loading_order(self, fs, config_dict, caplog):
        (repo_dict,) = config_dict["repositories"]

        manager = ConfigManager()
        for i, path in enumerate(manager.search_paths):
            repo_dict["name"] = str(i)
            repo_dict["path"] = str(path)
            config_str = yaml.dump(config_dict)
            fs.create_file(path, contents=config_str)

        config = manager.load()
        assert config.repositories == [
            RepositoryEntry(name=str(i), path=str(manager.search_paths[i]))
            for i in reversed(range(len(manager.search_paths)))
        ]
        assert not self.contains_warnings_in_log(caplog)

    def test_custom_search_patchs(self, fs, custom_config_dicts, caplog):
        for path, config_dict in custom_config_dicts:
            config_str = yaml.dump(config_dict)
            fs.create_file(path, contents=config_str)

        paths, config_dicts = zip(*custom_config_dicts)
        config = ConfigManager(paths).load()
        assert len(config.repositories) == len(config_dicts)
        assert not self.contains_warnings_in_log(caplog)

    def test_config_override(self, fs, config_dict, caplog):
        config_path = Path(ConfigManager.DEFAULT_SEARCH_PATHS[0]).expanduser()
        config_str = yaml.dump(config_dict)
        fs.create_file(config_path, contents=config_str)

        manager = ConfigManager()

        (repo_dict,) = config_dict["repositories"]

        config = manager.load()
        assert config.force_interface_compliance is True
        assert config.repositories == [RepositoryEntry(repo_dict["name"], repo_dict["path"])]

        override_config = Config(
            force_interface_compliance=False,
            repositories=None,
        )

        config2 = manager.load(override_config)
        assert config2.force_interface_compliance is False
        assert config2.repositories == [RepositoryEntry(repo_dict["name"], repo_dict["path"])]
        assert not self.contains_warnings_in_log(caplog)

    def test_loading_incorrect_configs(self, fs, incorrect_config_dicts, caplog):
        config_path = Path(ConfigManager.DEFAULT_SEARCH_PATHS[0]).expanduser()
        for incorrect_config in incorrect_config_dicts:
            manager = ConfigManager()
            config_str = yaml.dump(incorrect_config)
            fs.create_file(config_path, contents=config_str)
            manager.load()
            assert self.contains_warnings_in_log(caplog)
            config_path.unlink()
