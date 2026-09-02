# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Union

from topwrap.model.module import Module

DEFAULT_LOG_LEVEL = "WARNING"

LOG_FORMAT = "%(asctime)s  %(levelname)-8s %(name)s  %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


class LoggingColorFormatter(logging.Formatter):
    """Formatter that tints the whole log line according to its level.

    The timestamp and logger name are dimmed (keeping the level hue) and the
    level name is emphasised, so lines stay easy to scan. When ``use_color`` is
    false it emits the same layout without any escape sequences.
    """

    # 256-color foreground codes - soft hues that read well on light and dark terminals
    LEVEL_COLORS = {
        "DEBUG": "\033[38;5;245m",  # grey
        "INFO": "\033[38;5;110m",  # soft blue
        "WARNING": "\033[38;5;215m",  # amber
        "ERROR": "\033[38;5;203m",  # salmon red
        "CRITICAL": "\033[38;5;198m",  # magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    NORMAL = "\033[22m"  # reset bold/dim without dropping the color

    def __init__(self, use_color: bool = True) -> None:
        super().__init__(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt)
        message = record.getMessage()

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            message = f"{message}\n{record.exc_text}"
        if record.stack_info:
            message = f"{message}\n{self.formatStack(record.stack_info)}"

        if not self.use_color:
            return f"{timestamp}  {record.levelname:<8} {record.name}  {message}"

        color = self.LEVEL_COLORS.get(record.levelname, "")
        return (
            f"{color}"
            f"{self.DIM}{timestamp}{self.NORMAL}  "
            f"{self.BOLD}{record.levelname:<8}{self.NORMAL} "
            f"{self.DIM}{record.name}{self.NORMAL}  "
            f"{message}"
            f"{self.RESET}"
        )


def log_module_interfaces(logger: logging.Logger, module: Module) -> None:
    """
    :param logger: value got by invoking `logging.getLogger(__name__)`
    """

    interface_as_text = "interface of {} [".format(module.id.name)
    for port in module.ports:
        interface_as_text += " {} {},".format(port.name, port.direction.name)
    interface_as_text = interface_as_text[:-1] + " ]"
    logger.debug(interface_as_text)


def _set_color_handler() -> None:
    """Install (or replace) a stderr handler that colors log level names.

    Colors are only emitted when stderr is an interactive terminal.
    """

    root = logging.getLogger()
    for handler in list(root.handlers):
        # Only drop a handler we installed ourselves; leave any others alone.
        if getattr(handler, "_topwrap_color_handler", False):
            root.removeHandler(handler)

    use_color = (
        hasattr(sys.stderr, "isatty") and sys.stderr.isatty() and not os.environ.get("NO_COLOR")
    )

    handler = logging.StreamHandler(sys.stderr)
    handler._topwrap_color_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(LoggingColorFormatter(use_color=use_color))
    root.addHandler(handler)


def configure(log_level: Union[str, None], log_cfg: Union[Path, None]) -> None:
    """
    Function configuring logger based on `log_level` and `log_cfg` options
    """

    logging.getLogger().setLevel(DEFAULT_LOG_LEVEL)

    _set_color_handler()

    if log_cfg is not None:
        if not log_cfg.exists():
            logging.warning("Failed to find log config - {} - using defaults".format(log_cfg.name))
            return
        logging.config.fileConfig(log_cfg)

    if log_level is not None:
        logging.getLogger().setLevel(log_level)
        loggers = logging.root.manager.loggerDict
        for k in loggers.keys():
            if type(loggers[k]) is logging.Logger:
                loggers[k].setLevel(log_level)
