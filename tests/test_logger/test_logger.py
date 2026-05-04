# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path

import pytest

import topwrap.logger

logger = logging.getLogger()


class TestLogger:
    log_content = "logging from test_logger_using_level"

    def test_logger_using_level(self, caplog: pytest.LogCaptureFixture):
        level = "INFO"
        cfg_path = None
        topwrap.logger.configure(level, cfg_path)
        with caplog.at_level(level):
            logger.debug(self.log_content)
            logger.info(self.log_content)
            assert len(caplog.records) == 1

    def test_logger_using_default(self, caplog: pytest.LogCaptureFixture):
        level = None
        cfg_path = None
        topwrap.logger.configure(level, cfg_path)
        with caplog.at_level(topwrap.logger.DEFAULT_LOG_LEVEL):
            logger.debug(self.log_content)
            logger.info(self.log_content)
            logger.warning(self.log_content)
            assert len(caplog.records) == 1

    def test_logger_using_cfg(self):
        level = None
        dir_path = Path(os.getcwd()) / "tests" / "test_logger"
        cfg_path = dir_path / "logger.cfg"
        log_path = dir_path / "test.log"
        topwrap.logger.configure(level, cfg_path)
        logger.debug(self.log_content)
        logger.info(self.log_content)
        assert log_path.exists()
        line_count = 0
        log_file = open(log_path, "r")
        for _ in log_file:
            line_count = line_count + 1
        assert line_count == 2

    def test_logger_using_level_and_cfg(self):
        level = "INFO"
        dir_path = Path(os.getcwd()) / "tests" / "test_logger"
        cfg_path = dir_path / "logger.cfg"
        log_path = dir_path / "test.log"
        topwrap.logger.configure(level, cfg_path)
        logger.debug(self.log_content)
        logger.info(self.log_content)
        line_count = 0
        log_file = open(log_path, "r")
        for _ in log_file:
            line_count = line_count + 1
        assert line_count == 1
