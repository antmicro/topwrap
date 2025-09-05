# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Any, Optional

import click

from topwrap.util import get_config

logger = logging.getLogger(__name__)


class RepositoryPathParam(click.Path):
    """
    Handler for the repository CLI argument. Supports both a path
    to the repository or a name of the repository.
    """

    def convert(self, value: Any, param: Optional[Any], ctx: Optional[Any]) -> Path:
        if (
            isinstance(value, str)
            and (repo_path_cfg := get_config().repositories.get(value)) is not None
        ):
            return repo_path_cfg.to_path()
        else:
            return super().convert(value, param, ctx)
