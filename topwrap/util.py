# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from typing import Any, DefaultDict, Union


def removeprefix(s: str, prefix: str) -> str:
    """Returns string with a prefix removed if it contains it

    :param s: string to be stripped of its prefix
    :param prefix: prefix to be removed
    """
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


_R = DefaultDict[Any, Union["_R", Any]]


def recursive_defaultdict() -> _R:
    """Return defaultdict that can have many nested dicts inside without having to declare them"""
    return defaultdict(recursive_defaultdict)


def recursive_defaultdict_to_dict(recursive_defaultdict: _R) -> dict:
    """Convert recursive defaultdict to a dict"""
    for key, value in recursive_defaultdict.items():
        if isinstance(value, dict):
            recursive_defaultdict[key] = recursive_defaultdict_to_dict(value)
    return dict(recursive_defaultdict)
