# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""``topwrap library`` - manage libraries.

This is the FuseSoC-native replacement for ``topwrap repo``. The ``repo``
commands stay for now and will be removed once ``library`` is complete.
"""

import logging
import sys
from contextlib import contextmanager
from typing import Iterator, Optional

import cyclopts
from cyclopts.types import ExistingFile

from topwrap import library
from topwrap.cli import library_cli
from topwrap.config import _resolve_library_uris, library_scope
from topwrap.frontend.yaml.design_schema import DesignDescription

logger = logging.getLogger(__name__)


@contextmanager
def _design_config_scope(design: Optional[ExistingFile]) -> Iterator[None]:
    """Temporarily add a design YAML's ``config: libraries:``.

    Paths are resolved relative to the design file, matching how the design
    frontend applies them during a build.
    """
    if design is None:
        yield
        return

    desc = DesignDescription.load(design)
    libraries = desc.config.libraries if desc.config is not None else {}
    with library_scope(_resolve_library_uris(libraries, design.parent)):
        yield


@library_cli.command(name="add")
def add_library(
    name: str,
    uri: str,
    /,
):
    """Register a library in the local ``topwrap.yaml``.

    Parameters
    ----------
    name
        Name the library is referred to by.
    uri
        A local directory or a git URL.
    """
    try:
        library.add_library(name, uri)
    except library.LibraryError as e:
        logger.error("Could not add library '%s': %s", name, e)
        sys.exit(1)
    logger.info('Added library "%s" -> %s', name, uri)
    status = library.library_status(name, uri)
    if status:
        logger.info("Checked out at %s", status)


@library_cli.command(name="update")
def update(*names: str):
    """Fetch the latest upstream state of registered git libraries.

    Parameters
    ----------
    names
        Libraries to update. All registered libraries when omitted.
    """
    try:
        updated = library.update_libraries(tuple(names))
    except library.LibraryError as e:
        logger.error("Could not update libraries: %s", e)
        sys.exit(1)
    if not updated:
        logger.info("No git libraries to update.")
        return
    registered = library.list_libraries()
    for name in updated:
        status = library.library_status(name, registered[name])
        logger.info('Updated "%s"%s', name, f" -> {status}" if status else "")


list_cli = cyclopts.App(name="list", help="List registered libraries or their contents")
library_cli.command(list_cli)


def _library_line(name: str, uri: str) -> str:
    status = library.library_status(name, uri)
    return f'  "{name}" -> {uri}' + (f"  [{status}]" if status else "")


@list_cli.default
def list_registered(*, design: Optional[ExistingFile] = None):
    """List the registered libraries.

    Parameters
    ----------
    design
        Also include the libraries from this design YAML's ``config:`` section.
    """
    with _design_config_scope(design):
        libraries = library.list_libraries()
        if not libraries:
            print("No libraries registered.")
            return
        print("Registered libraries:")
        for name, uri in libraries.items():
            print(_library_line(name, uri))


def _print_contents(*, modules: bool, interfaces: bool, design: Optional[ExistingFile] = None):
    with _design_config_scope(design):
        libraries = library.list_libraries()
        if not libraries:
            print("No libraries registered.")
            return
        for name, uri in libraries.items():
            mods, ifaces = library.library_contents(name, uri)
            print(_library_line(name, uri))
            if modules:
                for vlnv in mods:
                    print(f"    module     {vlnv}")
            if interfaces:
                for vlnv in ifaces:
                    print(f"    interface  {vlnv}")


@list_cli.command(name="modules")
def list_modules(*, design: Optional[ExistingFile] = None):
    """List the IP modules provided by each library.

    Parameters
    ----------
    design
        Also include the libraries from this design YAML's ``config:`` section.
    """
    _print_contents(modules=True, interfaces=False, design=design)


@list_cli.command(name="interfaces")
def list_interfaces(*, design: Optional[ExistingFile] = None):
    """List the interface definitions provided by each library.

    Parameters
    ----------
    design
        Also include the libraries from this design YAML's ``config:`` section.
    """
    _print_contents(modules=False, interfaces=True, design=design)


@list_cli.command(name="all")
def list_all(*, design: Optional[ExistingFile] = None):
    """List both modules and interfaces provided by each library.

    Parameters
    ----------
    design
        Also include the libraries from this design YAML's ``config:`` section.
    """
    _print_contents(modules=True, interfaces=True, design=design)
