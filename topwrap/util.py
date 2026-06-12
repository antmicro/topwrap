# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from enum import Enum
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path
from typing import TYPE_CHECKING, Any, DefaultDict, Dict, Iterable, Optional, TypeVar, Union

from topwrap.model.misc import Identifier
from topwrap.repo.exceptions import ResourceNotFoundException

if TYPE_CHECKING:
    from topwrap.config import Config
    from topwrap.repo.user_repo import InterfaceDefinitionResource

JsonType = Dict[str, Any]

_SIMPLE_SV_LITERAL_PATTERN = (
    r"(?:"
    r"\d+"
    r"|(?:\d+'[sS]?[bBdDhHoO][0-9a-fA-F_xXzZ?]+)"
    r"|(?:'[sS]?[bBdDhHoO][0-9a-fA-F_xXzZ?]+)"
    r"|(?:'[01xXzZ])"
    r")"
)
_SIMPLE_SV_LITERAL_RE = re.compile(_SIMPLE_SV_LITERAL_PATTERN)
_PARENTHESIZED_SIMPLE_SV_LITERAL_RE = re.compile(rf"\(\s*({_SIMPLE_SV_LITERAL_PATTERN})\s*\)")


class ExistsStrategy(str, Enum):
    """
    How to behave when saving an arbitrary thing in an arbitrary
    location. Used commonly in e.g. `topwrap.repo`.
    """

    OVERWRITE = "overwrite"
    SKIP = "skip"
    RAISE = "raise"


def removeprefix(s: str, prefix: str) -> str:
    """Returns string with a prefix removed if it contains it

    :param s: string to be stripped of its prefix
    :param prefix: prefix to be removed
    """
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


def is_simple_sv_literal(text: str) -> bool:
    return _SIMPLE_SV_LITERAL_RE.fullmatch(text) is not None


def unwrap_simple_parenthesized_sv_literal(text: str) -> str:
    match = _PARENTHESIZED_SIMPLE_SV_LITERAL_RE.fullmatch(text.strip())
    return match.group(1) if match else text


_R = DefaultDict[Any, Union["_R", Any]]


def recursive_defaultdict() -> _R:
    """Return defaultdict that can have many nested dicts inside without having to declare them"""
    return defaultdict(recursive_defaultdict)


def recursive_defaultdict_to_dict(recursive_defaultdict: _R) -> Dict[Any, Any]:
    """Convert recursive defaultdict to a dict"""
    for key, value in recursive_defaultdict.items():
        if isinstance(value, DefaultDict):
            recursive_defaultdict[key] = recursive_defaultdict_to_dict(value)
    return dict(recursive_defaultdict)


class MissingType(Enum):
    """
    Marker type to be used when it's necessary to mark a field or a parameter as
    optional but when `None` should be treated as a supplied value, not a missing one.

    Implemented as an `Enum` because type-checkers know it's not possible to dynamically
    create new instances or add fields to an enum class. Knowing the defined fields are
    the only instances of the class, it's possible to narrow the type of a variable like
    `x: Union[T, MissingType]` to `T` only by checking if `x is not MISSING`, since
    `MISSING`/`MissingType.instance` is the only possible instance of the MissingType.

    Example::

        def func(param1: MaybeMissing[Any] = MISSING):
            if param1 is not MISSING:
                print(f"User passed: {param1}")
            else:
                print("missing value")

        func(None)
        >>> User passed: None

        func()
        >>> missing value
    """

    # the value assigned to this field doesn't
    # matter since there's no point in accessing it
    instance = None


_T = TypeVar("_T")
# Note, that because an enum variant is an instance of its own type
# `MISSING != None` and `MISSING is not None` despite what may seem
# by just analyzing the assignments.
MISSING = MissingType.instance
MaybeMissing = Union[_T, MissingType]


class UnreachableError(RuntimeError):
    """Marks a code path as unreachable, giving a hint to the typechecker, while still raising in
    case of a logic error"""

    def __init__(self, *args: object) -> None:
        super().__init__("Stepped into a code path marked as unreachable", *args)


def read_json_file(json_file_path: Path) -> JsonType:
    with open(json_file_path, "r") as json_file:
        json_contents = json.load(json_file)
    return json_contents


def save_file_to_json(file_path: Path, file_name: str, file_content: JsonType):
    file_path.mkdir(parents=True, exist_ok=True)
    with open(Path(file_path / file_name), "w") as json_file:
        json.dump(file_content, json_file)


def path_relative_to(org_path: Path, rel_to: Path) -> Path:
    """Return `org_path` converted to be relative to `rel_to`.

    This is a backport of `pathlib.Path.relative_to(rel_to, walk_up=True)` which
    was added in Python 3.12:
    https://github.com/python/cpython/blob/3.12/Lib/pathlib.py#L663
    """

    step = None
    for _step, path in enumerate([rel_to] + list(rel_to.parents)):
        step = _step
        if path == org_path or path in org_path.parents:
            break
        elif path.name == "..":
            raise ValueError(f"'..' segment in {str(rel_to)!r} cannot be walked")
    else:
        raise ValueError(f"{str(org_path)!r} and {str(rel_to)!r} have different anchors")
    parts = ("..",) * step + org_path.parts[len(path.parts) :]
    return type(org_path)(*parts)


def _resolve_caliptra_var_path(path: str, caliptra_path: Path) -> Path:
    resolved = (
        path.replace("${CALIPTRA_ROOT}", str(caliptra_path))
        .replace("${CALIPTRA_PRIM_ROOT}", str(caliptra_path / "src/caliptra_prim"))
        .replace("${CALIPTRA_PRIM_MODULE_PREFIX}", "caliptra_prim")
    )
    return Path(resolved)


def collect_filelist_sources(
    filelist_path: Path,
    *,
    sourcefiles: Iterable[Path] | None = None,
    base_sources: Iterable[Path] = (),
) -> tuple[list[Path], set[Path]]:
    """Collect Caliptra SV source files and include directories from `.vf` manifests."""
    sv_sources = set(base_sources)
    include_dirs: set[Path] = set()

    vf_files = set(sourcefiles) if sourcefiles is not None else set(filelist_path.rglob("*.vf"))
    for vf_path in vf_files:
        with open(vf_path) as vf:
            for line in vf:
                entry = line.strip()
                if entry.startswith("+incdir+"):
                    include_dir = _resolve_caliptra_var_path(
                        entry.split("+incdir+", 1)[1], filelist_path
                    )
                    if include_dir.exists():
                        include_dirs.add(include_dir)
                    continue

                sv_path = _resolve_caliptra_var_path(entry, filelist_path)
                if sv_path.exists():
                    sv_sources.add(sv_path)

    return list(sv_sources), include_dirs


def get_interface_by_id(id: Identifier) -> Optional["InterfaceDefinitionResource"]:
    from topwrap.repo.user_repo import InterfaceDefinitionResource

    for repo in get_config().loaded_repos.values():
        try:
            res = repo.get_resource(InterfaceDefinitionResource, id.combined())
        except ResourceNotFoundException:
            continue
        return res


def get_config() -> Config:
    """Accessor for the global configuration instance. Useful
    for situations where plainly importing `topwrap.config.config`
    would result in a dependency cycle.
    """

    from topwrap.config import config

    return config


def get_package_identifier(package_name: str) -> str:
    """Return the identifier of an installed Python package as a string

    For packages installed from a Git repository, the commit SHA is returned.
    For packages installed from a standard distribution, the version is returned.
    """

    result = "unknown"
    try:
        dist = distribution(package_name)
    except PackageNotFoundError:
        logging.warning(f"Unable to get identifier for {package_name}, package not found")
        return "unknown"

    try:
        data = json.loads(dist.read_text("direct_url.json"))
        return data.get("vcs_info", {}).get("commit_id", result)
    except FileNotFoundError:
        logging.info(f"Unable to get SHA of {package_name}")
        pass

    logging.info(f"Using {package_name} package version as identifier")
    return version(package_name)
