# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import copy

import fusesoc.utils
import pytest
import yaml

# fusesoc's C-accelerated YAML loader crashes when a trace function is active
# (e.g. under `pytest --cov`). The pure-Python loader is unaffected and not
# perceptibly slower for anything this suite does.
fusesoc.utils.YamlLoader = yaml.SafeLoader

from topwrap.config import config  # noqa: E402
from topwrap.library import clear_index_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _restore_global_config():
    """Undo mutations tests make to the process-wide ``topwrap.config.config``.

    Some tests (e.g. anything driving the deprecated ``--repo`` CLI flag)
    call ``update_repo``/``update_libraries`` on the shared config singleton.
    Without this, those changes leak into unrelated tests that run later in
    the same session.
    """
    repositories = copy.copy(config.repositories)
    libraries = copy.copy(config.libraries)
    force_interface_compliance = config.force_interface_compliance

    yield

    # Only touch the shared caches when a test actually mutated the config;
    # unconditionally clearing them would force every subsequent test to
    # reload repos/libraries from disk, which some tests' log assertions
    # aren't expecting.
    if (
        config.repositories == repositories
        and config.libraries == libraries
        and config.force_interface_compliance == force_interface_compliance
    ):
        return

    config.repositories = repositories
    config.libraries = libraries
    config.force_interface_compliance = force_interface_compliance
    config._clear_cached_repo()
    clear_index_cache()
