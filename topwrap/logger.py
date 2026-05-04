# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import logging.config
from pathlib import Path
from typing import Union

from topwrap.model.module import Module

DEFAULT_LOG_LEVEL = "WARNING"


def log_module_interfaces(logger: logging.Logger, module: Module) -> None:
    """
    :param logger: value got by invoking `logging.getLogger(__name__)`
    """

    interface_as_text = "interface of {} [".format(module.id.name)
    for port in module.ports:
        interface_as_text += " {} {},".format(port.name, port.direction.name)
    interface_as_text = interface_as_text[:-1] + " ]"
    logger.debug(interface_as_text)


def configure(log_level: Union[str, None], log_cfg: Union[Path, None]) -> None:
    """
    Function configuring logger based on `log_level` and `log_cfg` options
    """

    logging.basicConfig(level=DEFAULT_LOG_LEVEL)
    logging.getLogger().setLevel(DEFAULT_LOG_LEVEL)

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
