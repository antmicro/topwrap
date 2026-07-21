# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from topwrap.util import get_package_identifier

kpm_sha = get_package_identifier("pipeline_manager")
DEFAULT_SERVER_BASE_DIR = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.local/cache")).expanduser()
    / "topwrap/kpm_build"
    / kpm_sha
)
DEFAULT_WORKSPACE_DIR = "workspace"
DEFAULT_BACKEND_DIR = "backend"
DEFAULT_FRONTEND_DIR = "frontend"
DEFAULT_SERVER_ADDR = "127.0.0.1"
DEFAULT_SERVER_PORT = 9000
DEFAULT_BACKEND_ADDR = "127.0.0.1"
DEFAULT_BACKEND_PORT = 5000
