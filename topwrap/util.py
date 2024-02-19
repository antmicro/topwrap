# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Dict, Generator, List, Union

from .interface import get_interface_by_prefix


def check_interface_compliance(iface_def, signals):
    """Check if list of signal names matches the names in interface definition

    :return: bool
    """
    required = iface_def.signals["required"]
    optional = iface_def.signals["optional"]

    for name in required:
        if name not in signals:
            return False
    for name in signals:
        if name not in required and name not in optional:
            return False
    return True


def removeprefix(s: str, prefix: str) -> str:
    """Return string with a prefix removed if it contains it

    :param s: string to be stripped of its prefix
    :param prefix: prefix to be removed
    """
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s
