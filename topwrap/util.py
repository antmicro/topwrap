# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


from collections import defaultdict
from typing import Any, DefaultDict, Union


def removeprefix(s: str, prefix: str) -> str:
    """Return string with a prefix removed if it contains it

    :param s: string to be stripped of its prefix
    :param prefix: prefix to be removed
    """
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


_R = DefaultDict[Any, Union["_R", Any]]


def recursive_defaultdict() -> _R:
    return defaultdict(recursive_defaultdict)
