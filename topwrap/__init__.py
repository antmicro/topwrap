# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import os

if (var := "AMARANTH_USE_YOSYS") not in os.environ:
    os.environ[var] = "builtin"

try:
    # This determines the version from editable installs
    from setuptools_scm import get_version

    __version__ = get_version(root="..", relative_to=__file__)
except (ImportError, LookupError):
    # This determines the version from installed packages
    try:
        from ._version import __version__
    except ImportError:
        from importlib.metadata import PackageNotFoundError, version

        try:
            __version__ = version("topwrap")
        except PackageNotFoundError:
            __version__ = "0.0.0+unknown"
