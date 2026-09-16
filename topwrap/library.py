# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""Management of libraries used by topwrap.

A *library* is a directory (local, or a git repository) of CAPI2 ``.core``
files. The registry - a ``name -> uri`` mapping - is stored in topwrap's own
configuration (the ``libraries:`` section of ``topwrap.yaml``). Resolving a
library into cores uses the FuseSoC infrastructure directly.

Git libraries are checked out into a project-local ``.fusesoc-cores/``
directory (next to ``topwrap.yaml``), not a shared machine-global location, so
different projects never contend over the same checkout.

This is the FuseSoC-native successor to :mod:`topwrap.repo`.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from fusesoc.config import Config
from fusesoc.coremanager import CoreManager
from fusesoc.librarymanager import Library, LibraryManager
from fusesoc.provider.provider import get_provider

from topwrap import fuse_schema
from topwrap.backend.yaml.common.interface_schema import InterfaceDefinitionDescription
from topwrap.frontend.yaml.interface import InterfaceDefinitionDescriptionFrontend
from topwrap.util import get_config, path_relative_to

if TYPE_CHECKING:
    from fusesoc.capi2.core import CoreInterface

    from topwrap.model.interface import InterfaceDefinition
    from topwrap.model.misc import Identifier

logger = logging.getLogger(__name__)


class LibraryError(Exception):
    """Raised when a library cannot be registered, read, or resolved."""


#: ``file_type`` marking an individual ``.core`` fileset file as a topwrap IP
#: module description (a ``module.yaml``).
TOPWRAP_MODULE_FILE_TYPE = "topwrapModule"

#: ``file_type`` marking an individual ``.core`` fileset file as a topwrap
#: interface definition.
TOPWRAP_INTERFACE_FILE_TYPE = "topwrapInterface"

#: Project-local directory (relative to the working directory) that git
#: libraries are checked out into.
LIBRARY_CHECKOUT_DIR = Path(".fusesoc-cores")


# --------------------------------------------------------------------------- #
# Registry (topwrap config)
# --------------------------------------------------------------------------- #


def list_libraries() -> dict[str, str]:
    """The registered ``name -> uri`` libraries."""
    return dict(get_config().libraries)


def _validate_library_name(name: str) -> None:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None:
        raise LibraryError(f"invalid library name '{name}'; use letters, digits, '.', '_' or '-'")


def add_library(name: str, uri: str) -> None:
    """Register a library in the local ``topwrap.yaml`` and check it out.

    Git libraries are cloned into ``.fusesoc-cores/`` right away; the registry
    entry is only written once that succeeds.

    :param name: name the library is referred to by
    :param uri: a local directory or a git URL
    :raises LibraryError: the name is taken, or the library could not be fetched
    """
    _validate_library_name(name)
    if name in get_config().libraries:
        raise LibraryError(f"library '{name}' is already registered")

    try:
        _fusesoc_library(name, uri)
    except LibraryError:
        raise
    except Exception as e:
        raise LibraryError(f"could not fetch library from '{uri}': {e}") from e

    from topwrap.config import ConfigManager

    config_path = ConfigManager.DEFAULT_SEARCH_PATHS[0]  # topwrap.yaml in the cwd
    data = yaml.safe_load(config_path.read_text()) if config_path.is_file() else {}
    data = data or {}
    data.setdefault("libraries", {})[name] = uri
    config_path.write_text(yaml.safe_dump(data, sort_keys=False))

    get_config().libraries[name] = uri  # reflect it in the running process
    clear_index_cache()


# --------------------------------------------------------------------------- #
# Packaging (writing a library-shaped ``.core`` file)
# --------------------------------------------------------------------------- #

#: HDL/constraint file extensions recognized when listing sources in a
#: written ``.core``'s ``rtl`` fileset, mapped to their CAPI2 ``file_type``.
#: Anything else falls back to the generic ``user`` type.
_SOURCE_FILE_TYPES = {
    ".v": "verilogSource",
    ".vh": "verilogSource",
    ".sv": "systemVerilogSource",
    ".svh": "systemVerilogSource",
    ".vhd": "vhdlSource",
    ".vhdl": "vhdlSource",
    ".xdc": "xdc",
}


def _source_file_type(path: Path) -> str:
    return _SOURCE_FILE_TYPES.get(path.suffix.lower(), "user")


def write_module_core(
    core_path: Path, vlnv: Identifier, module_yaml: Path, sources: Iterable[Path] = ()
) -> None:
    """Write a CAPI2 ``.core`` file at ``core_path`` for a single module.

    The ``.core`` gets a ``topwrap`` fileset pointing at ``module_yaml`` with
    ``file_type: topwrapModule``, and (if given) an ``rtl`` fileset listing
    ``sources`` typed by extension - the shape a ``topwrap library`` expects.
    ``module_yaml`` and ``sources`` are written as paths relative to
    ``core_path``'s own directory, so the package stays portable.

    :param core_path: where to write the ``.core`` file
    :param vlnv: identifier the ``.core`` (and the module it describes) is
        known by
    :param module_yaml: path of the module's IP description YAML
    :param sources: HDL source files to list in an ``rtl`` fileset
    """
    base = core_path.resolve().parent
    module_yaml_rel = path_relative_to(module_yaml.resolve(), base)

    filesets = {
        "topwrap": fuse_schema.FileSet(
            files=[
                fuse_schema.FileSource(
                    name=str(module_yaml_rel), file_type=TOPWRAP_MODULE_FILE_TYPE
                )
            ],
            depend=[],
        ),
    }

    rtl_files = []
    for src in sources:
        src_rel = path_relative_to(src.resolve(), base)
        rtl_files.append(
            fuse_schema.FileSource(name=str(src_rel), file_type=_source_file_type(src))
        )
    targets = {}
    if rtl_files:
        filesets["rtl"] = fuse_schema.FileSet(files=rtl_files, depend=[])
        targets["default"] = fuse_schema.ToolTarget(
            filesets=["rtl"], toplevel="", hooks={}, default_tool="", tools={}
        )

    core = fuse_schema.Core(
        name=fuse_schema.VLNV_S(vlnv.vendor, vlnv.library, vlnv.name, vlnv.version),
        description="Package generated by 'topwrap package'",
        filesets=filesets,
        targets=targets,
        scripts={},
    )
    core_path.write_text(core.to_yaml())


# --------------------------------------------------------------------------- #
# Contents (FuseSoC)
# --------------------------------------------------------------------------- #


def _split_git_ref(uri: str) -> tuple[str, str | None]:
    """Split a trailing ``@<ref>`` (branch / tag / commit) off a git URI.

    ``https://host/repo.git@main`` -> ``("https://host/repo.git", "main")``.
    Only an ``@`` that follows the repository path is treated as a ref
    separator, so neither the userinfo of a URL (``https://token@host/repo``)
    nor the ``user@host`` of an ``scp``-like URL (``git@host:repo.git``) is
    mistaken for one. A URI without such an ``@`` yields ``(uri, None)``.
    """
    scheme, sep, body = uri.partition("://")
    if not sep:
        scheme, body = "", uri

    head = ""
    if sep:
        # an "@" before the first "/" belongs to the authority, not to a ref
        authority, slash, body = body.partition("/")
        head = f"{authority}{slash}"
    elif "@" in body and ":" in body and body.index("@") < body.index(":"):
        # scp-like "user@host:path" - protect the leading "user@"
        user, _, body = body.partition("@")
        head = f"{user}@"

    path, at, ref = body.rpartition("@")
    if not at:
        return uri, None
    return f"{scheme}{sep}{head}{path}", ref


def _is_remote_uri(uri: str) -> bool:
    """Whether a library URI names a remote repository rather than a directory.

    Decided by the shape of the URI alone, so that a local path that is missing
    is reported as such instead of being attempted as a clone.
    """
    if "://" in uri:
        return True
    authority, sep, _ = uri.partition(":")
    # scp-like "user@host:path"
    return bool(sep) and "@" in authority


def _fusesoc_library(name: str, uri: str):
    """A ``fusesoc.librarymanager.Library`` for a registered library.

    Git libraries are checked out (once) into the project-local
    ``.fusesoc-cores/`` directory. A ``@<ref>`` suffix on a git URI selects the
    branch / tag / commit to check out.

    :raises LibraryError: the URI names a local directory that does not exist
    """
    _validate_library_name(name)
    if not _is_remote_uri(uri):
        local = Path(uri).expanduser()
        if not local.is_dir():
            raise LibraryError(f"'{uri}' is not a directory")
        location = str(local.resolve())
        return Library(name, location, "local", location)

    git_uri, ref = _split_git_ref(uri)
    checkout = _checkout_root() / name
    library = Library(name, str(checkout), "git", git_uri, ref, True)
    if checkout.exists():
        if checkout.is_symlink() or not (checkout / ".git").is_dir():
            raise LibraryError(f"existing checkout '{checkout}' is not a git repository")
        result = subprocess.run(
            ["git", "-C", str(checkout), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
        )
        origin = result.stdout.strip()
        if result.returncode != 0 or origin != git_uri:
            actual = origin or "no origin"
            raise LibraryError(
                f"existing checkout '{checkout}' belongs to '{actual}', not '{git_uri}'"
            )
    else:
        try:
            get_provider("git").init_library(library)
        except Exception:
            if checkout.exists():
                shutil.rmtree(checkout, ignore_errors=True)
            raise
    return library


def _checkout_root() -> Path:
    """The project-local checkout directory, created on first use."""
    root = LIBRARY_CHECKOUT_DIR
    if not root.exists():
        root.mkdir(parents=True)
        (root / ".gitignore").write_text("*\n")
    return root


def update_libraries(names: tuple[str, ...] = ()) -> list[str]:
    """Fetch the latest upstream state of registered git libraries.

    Local-directory libraries are skipped. A git library that has not been
    checked out yet is cloned.

    :param names: libraries to update; all registered ones when empty
    :returns: the names of the git libraries that were updated
    :raises LibraryError: one of ``names`` is not registered
    """
    registered = list_libraries()
    selected = list(names) if names else list(registered)
    unknown = sorted(n for n in selected if n not in registered)
    if unknown:
        raise LibraryError(f"not registered: {', '.join(unknown)}")

    manager = LibraryManager()
    git_libs: list[str] = []
    for name in selected:
        library = _fusesoc_library(name, registered[name])
        manager.add_library(library)
        if library.sync_type != "local":
            git_libs.append(name)

    if git_libs:
        manager.update(git_libs)
        clear_index_cache()
    return git_libs


def library_status(name: str, uri: str) -> str | None:
    """A short description of a git library's current checkout.

    ``None`` for local-directory libraries and for git libraries that have not
    been checked out yet.
    """
    _validate_library_name(name)
    if Path(uri).expanduser().is_dir():
        return None
    checkout = LIBRARY_CHECKOUT_DIR / name
    if not (checkout / ".git").exists():
        return None

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(checkout), *args], capture_output=True, text=True
        ).stdout.strip()

    described = git("describe", "--tags", "--always", "--dirty")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch and branch != "HEAD":
        return f"{branch} ({described})" if described else branch
    return described or None


def _core_manager(name: str, uri: str) -> CoreManager:
    config = Config(create_if_missing=False)
    core_manager = CoreManager(config)
    core_manager.add_library(_fusesoc_library(name, uri), config.ignored_dirs)
    return core_manager


@dataclass(frozen=True)
class _LibraryFile:
    """A fileset file together with the CAPI2 core that owns it."""

    file_type: str
    path: Path
    core_vlnv: str


def _iter_fileset_files(core: CoreInterface) -> Iterator[_LibraryFile]:
    """Yield every fileset file and its owning CAPI2 core.

    ``file_type`` is resolved per file: an entry's own ``file_type`` wins over
    the fileset-level default, so a single fileset may mix ``topwrapModule``,
    ``topwrapInterface`` and plain source files.
    """
    root = Path(getattr(core, "files_root", None) or core.core_root)
    core_vlnv = str(core.name)
    for fileset in core.get_data({}).filesets.values():
        default_type = fileset.file_type or ""
        for entry in fileset.files:
            if isinstance(entry, dict):
                for fname, attrs in entry.items():
                    file_type = getattr(attrs, "file_type", None) or default_type
                    yield _LibraryFile(file_type, root / fname, core_vlnv)
            else:
                yield _LibraryFile(default_type, root / str(entry), core_vlnv)


def _identify(path: Path) -> str:
    """A ``vendor:library:name:version`` id for a topwrap description file.

    Falls back to the file name when the ``id`` cannot be read.
    """
    try:
        data = yaml.safe_load(path.read_text()) or {}
        ident = data.get("id")
        if isinstance(ident, str):
            return ident
        if isinstance(ident, dict) and ident.get("name"):
            return ":".join(
                (
                    ident.get("vendor", "vendor"),
                    ident.get("library", "libdefault"),
                    ident["name"],
                    str(ident.get("version", "0.1")),
                )
            )
    except (OSError, yaml.YAMLError):
        pass
    return path.name


def _library_files(name: str, uri: str) -> Iterator[_LibraryFile]:
    """Yield every fileset file of every core in a library."""
    for core in _core_manager(name, uri).get_cores().values():
        yield from _iter_fileset_files(core)


def library_contents(name: str, uri: str) -> tuple[list[str], list[str]]:
    """``(module ids, interface ids)`` provided by a library.

    A single ``.core`` may contribute any number of modules and interfaces -
    one per file marked ``topwrapModule`` / ``topwrapInterface``.
    """
    modules: list[str] = []
    interfaces: list[str] = []
    for file in _library_files(name, uri):
        if file.file_type == TOPWRAP_MODULE_FILE_TYPE:
            modules.append(_identify(file.path))
        elif file.file_type == TOPWRAP_INTERFACE_FILE_TYPE:
            interfaces.append(_identify(file.path))
    return sorted(modules), sorted(interfaces)


# --------------------------------------------------------------------------- #
# VLNV resolution
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _LibraryRegistration:
    """Name and URI of one library in an index-cache snapshot."""

    name: str
    uri: str


@dataclass(frozen=True)
class _LibraryModule:
    """A Topwrap module description and its owning CAPI2 core."""

    path: Path
    core_vlnv: str


@dataclass(frozen=True)
class _LibraryIndexes:
    """VLNV-to-description-path indexes for registered library resources."""

    modules: dict[str, _LibraryModule]
    interfaces: dict[str, Path]


_LibrarySnapshot = tuple[_LibraryRegistration, ...]


def _frozen_libs() -> _LibrarySnapshot:
    return tuple(_LibraryRegistration(name, uri) for name, uri in sorted(list_libraries().items()))


#: Memoized only once every library reads cleanly, so a briefly unreadable
#: one isn't remembered as empty.
_INDEX_CACHE: dict[_LibrarySnapshot, _LibraryIndexes] = {}


def _indexes(libs: _LibrarySnapshot) -> _LibraryIndexes:
    cached = _INDEX_CACHE.get(libs)
    if cached is not None:
        return cached

    modules: dict[str, _LibraryModule] = {}
    interfaces: dict[str, Path] = {}
    complete = True
    for library in libs:
        try:
            files = list(_library_files(library.name, library.uri))
        except Exception as e:  # noqa: BLE001 - one bad library must not hide the rest
            logger.warning("could not read library '%s' (%s): %s", library.name, library.uri, e)
            complete = False
            continue
        for file in files:
            if file.file_type == TOPWRAP_MODULE_FILE_TYPE:
                vlnv = _identify(file.path)
                module = _LibraryModule(file.path, file.core_vlnv)
                if vlnv in modules and modules[vlnv] != module:
                    raise LibraryError(
                        f"duplicate VLNV '{vlnv}' in registered libraries: "
                        f"{modules[vlnv].path} and {file.path}"
                    )
                modules[vlnv] = module
            elif file.file_type == TOPWRAP_INTERFACE_FILE_TYPE:
                vlnv = _identify(file.path)
                if vlnv in interfaces and interfaces[vlnv] != file.path:
                    raise LibraryError(
                        f"duplicate VLNV '{vlnv}' in registered libraries: "
                        f"{interfaces[vlnv]} and {file.path}"
                    )
                interfaces[vlnv] = file.path

    indexes = _LibraryIndexes(modules, interfaces)
    if complete:
        _INDEX_CACHE[libs] = indexes
    return indexes


def clear_index_cache() -> None:
    """Drop the memoized VLNV -> file / definition indexes (call after add/update)."""
    _INDEX_CACHE.clear()
    _IFACE_CACHE.clear()


def module_index() -> dict[str, Path]:
    """``{vlnv: module-description path}`` across all registered libraries."""
    return {vlnv: module.path for vlnv, module in _indexes(_frozen_libs()).modules.items()}


def library_core_of(file: Path) -> str | None:
    """The VLNV a registered library provides ``file`` under, if any.

    Lets a backend name a module by ``core:`` instead of its file path.
    """
    try:
        target = Path(file).resolve()
    except OSError:
        return None
    for vlnv, module in _indexes(_frozen_libs()).modules.items():
        if module.path.resolve() == target:
            return vlnv
    return None


def fusesoc_core_of(file: Path) -> str | None:
    """The owning CAPI2 core VLNV for a registered module description."""
    try:
        target = Path(file).resolve()
    except OSError:
        return None
    for module in _indexes(_frozen_libs()).modules.values():
        if module.path.resolve() == target:
            return module.core_vlnv
    return None


def interface_index() -> dict[str, Path]:
    """``{vlnv: interface-description path}`` across all registered libraries."""
    return dict(_indexes(_frozen_libs()).interfaces)


def _vlnv_matches(key: str, query: str) -> bool:
    """Whether a full ``vendor:library:name:version`` key satisfies ``query``.

    ``query`` may be partial: fields are matched right-aligned onto
    ``vendor:library:name`` (so a bare ``name`` works), an empty field is a
    wildcard (``:utils:fifo``), and a 4-field query also constrains the version.
    """
    key_fields = key.split(":")
    query_fields = query.split(":")
    if len(query_fields) > 4 or len(key_fields) != 4:
        return key == query
    width = 4 if len(query_fields) == 4 else 3
    key_fields = key_fields[:width]
    query_fields = [""] * (width - len(query_fields)) + query_fields
    return all(q in ("", k) for q, k in zip(query_fields, key_fields, strict=True))


def _resolve(query: str, index: dict[str, Path], kind: str) -> Path:
    if query in index:
        return index[query]
    matches = sorted(k for k in index if _vlnv_matches(k, query))
    if len(matches) == 1:
        return index[matches[0]]
    if not matches:
        available = ", ".join(sorted(index)) or "none"
        raise LibraryError(
            f"no {kind} matches '{query}' in registered libraries (available: {available})"
        )
    raise LibraryError(f"{kind} reference '{query}' is ambiguous, matches: {', '.join(matches)}")


def resolve_module(vlnv: str) -> Path:
    """Path of the ``topwrapModule`` description file for ``vlnv``.

    ``vlnv`` may be a full ``vendor:library:name:version`` or a partial form
    (see :func:`_vlnv_matches`). Raises :class:`LibraryError` on no / ambiguous
    match.
    """
    return _resolve(vlnv, module_index(), "module")


def resolve_interface(vlnv: str) -> Path:
    """Path of the ``topwrapInterface`` description file for ``vlnv`` (see
    :func:`resolve_module`)."""
    return _resolve(vlnv, _indexes(_frozen_libs()).interfaces, "interface")


_IFACE_CACHE: dict[_LibrarySnapshot, dict[str, "InterfaceDefinition"]] = {}


def _interface_defs(libs: _LibrarySnapshot) -> dict[str, InterfaceDefinition]:
    cached = _IFACE_CACHE.get(libs)
    if cached is not None:
        return cached

    out: dict[str, InterfaceDefinition] = {}
    for vlnv, path in _indexes(libs).interfaces.items():
        try:
            desc = InterfaceDefinitionDescription.from_yaml(path.read_text())
            out[vlnv] = InterfaceDefinitionDescriptionFrontend().parse(desc)
        except Exception as e:  # noqa: BLE001 - a bad file must not break the rest
            logger.warning("could not load interface '%s' from %s: %s", vlnv, path, e)

    # Only worth keeping if the index it was built from was itself complete.
    if libs in _INDEX_CACHE:
        _IFACE_CACHE[libs] = out
    return out


def interface_definitions() -> list[InterfaceDefinition]:
    """Parsed IR interface definitions from every registered library."""
    return list(_interface_defs(_frozen_libs()).values())


def resolve_interface_definition(vlnv: str) -> InterfaceDefinition | None:
    """The IR interface definition matching ``vlnv`` (full or partial), or
    ``None`` when there is no unambiguous match."""
    defs = _interface_defs(_frozen_libs())
    if vlnv in defs:
        return defs[vlnv]
    matches = [k for k in defs if _vlnv_matches(k, vlnv)]
    return defs[matches[0]] if len(matches) == 1 else None
