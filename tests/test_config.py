# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml

from topwrap.config import Config, ConfigManager
from topwrap.resource_field import FileReferenceHandler, UriReferenceHandler


class TestConfigManager:
    @pytest.fixture
    def config_dict(self):
        return Config(
            force_interface_compliance=True,
            repositories={
                "my_repo": FileReferenceHandler("~/custom/repo/path"),
            },
        ).to_dict()

    @pytest.fixture
    def custom_config_dicts(self):
        return [
            (
                Path("custom/path/cfg.yaml"),
                Config(repositories={"repo1": FileReferenceHandler("path1")}).to_dict(),
            ),
            (
                Path("/global/path/mycfg.yaml"),
                Config(repositories={"repo2": FileReferenceHandler("path2")}).to_dict(),
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
                "meta": (
                    "A missing 'repositories' entry is correct, an additional custom entry is not"
                ),
            },
        ]

    @staticmethod
    def contains_warnings_in_log(caplog):
        for name, level, _msg in caplog.record_tuples:
            if name == "topwrap.config" and level == logging.WARNING:
                return True
        return False

    def test_adding_repo_duplicates_and_order(self):
        configs = [
            Config(repositories={"my_repo": FileReferenceHandler("./foo")}),
            Config(
                repositories={
                    "my_repo": FileReferenceHandler("./bar"),
                    "zwei_repo": UriReferenceHandler("https://antmicro.com"),
                }
            ),
            Config(repositories={"my_repo": FileReferenceHandler("./baz")}),
        ]

        files = []

        for conf in configs:
            f = NamedTemporaryFile()
            conf.save(Path(f.name))
            files.append(f)

        manager = ConfigManager([Path(f.name) for f in files])
        conf = manager.load()

        assert len(conf.repositories) == 2
        assert conf.repositories["my_repo"].to_str().endswith("foo")

    def test_config_override(self, config_dict, caplog):
        with NamedTemporaryFile(mode="w+") as tmp:
            config_str = yaml.dump(config_dict)
            tmp.write(config_str)
            tmp.flush()

            manager = ConfigManager([Path(tmp.name)])
            config = manager.load()
            assert config.force_interface_compliance is True
            assert config.repositories["my_repo"].value == "~/custom/repo/path"

            override_config = Config(
                force_interface_compliance=False,
                repositories={},
            )

            config2 = manager.load(override_config)
            assert config2.force_interface_compliance is False
            assert config.repositories["my_repo"].value == "~/custom/repo/path"
            assert not self.contains_warnings_in_log(caplog)

    def test_loading_incorrect_configs(self, incorrect_config_dicts, caplog):
        with NamedTemporaryFile(mode="w+") as config_path:
            for incorrect_config in incorrect_config_dicts:
                manager = ConfigManager([Path(config_path.name)])
                config_str = yaml.dump(incorrect_config)
                config_path.write(config_str)
                config_path.flush()
                manager.load()
                assert self.contains_warnings_in_log(caplog)
