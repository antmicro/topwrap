# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

"""``topwrap package`` - package a single IP module from its HDL sources."""

import logging
import sys
from pathlib import Path
from typing import Annotated, List, Optional, Tuple

from cyclopts import Parameter
from cyclopts.types import ExistingFile

from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.cli import cli, load_interfaces_from_repos, load_modules_from_repos
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.library import write_module_core
from topwrap.model.inference.inference import infer_interfaces_from_module, parse_grouping_hints
from topwrap.model.misc import Identifier
from topwrap.util import parse_params

logger = logging.getLogger(__name__)


def _resolve(base: Path, path: Path) -> Path:
    return path if path.is_absolute() else base / path


def _classify_token(
    tok: str, base: Path, files: List[Path], incdirs: List[Path], defines: List[str]
) -> None:
    """Classify one EDA-tool-standard token into ``files``/``incdirs``/``defines``.

    Recognizes ``+incdir+<dir>[+<dir>...]`` and
    ``+define+<name>[=<value>][+<name>[=<value>]...]``; anything else must be
    an existing source file path. Relative paths are resolved against
    ``base`` (the current directory for a CLI token, or a filelist's own
    directory for one of its entries).
    """
    if tok.startswith("+incdir+"):
        incdirs.extend(_resolve(base, Path(p)) for p in parse_params("+incdir+", tok))
    elif tok.startswith("+define+"):
        defines.extend(parse_params("+define+", tok))
    else:
        path = _resolve(base, Path(tok))
        if not path.is_file():
            logger.error(f"'{tok}' is not a file")
            sys.exit(1)
        files.append(path)


def _read_filelist(path: Path, files: List[Path], incdirs: List[Path], defines: List[str]) -> None:
    """Expand a VCS/Verilator-style ``-f`` filelist into ``files``,
    ``incdirs``, and ``defines``, recursively following nested ``-f``/``-F``
    references. Blank lines and ``//`` comments are ignored. Relative paths
    are resolved against the filelist's own directory.
    """
    base = path.parent
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("-f ") or line.startswith("-F "):
            nested = _resolve(base, Path(line[3:].strip()))
            if not nested.is_file():
                logger.error(f"'{nested}' is not a file")
                sys.exit(1)
            _read_filelist(nested, files, incdirs, defines)
        else:
            _classify_token(line, base, files, incdirs, defines)


def _collect_sources(
    sources: Tuple[str, ...], filelists: Tuple[Path, ...]
) -> Tuple[List[Path], List[Path], List[str]]:
    files: List[Path] = []
    incdirs: List[Path] = []
    defines: List[str] = []
    for f in filelists:
        _read_filelist(f, files, incdirs, defines)
    for tok in sources:
        _classify_token(tok, Path("."), files, incdirs, defines)
    return files, incdirs, defines


@cli.command(name="package")
def package_main(
    sources: Annotated[Tuple[str, ...], Parameter(alias="-s")] = (),
    *,
    flist: Annotated[Tuple[ExistingFile, ...], Parameter(alias="-f")] = (),
    output: Annotated[Optional[Path], Parameter(alias="-o")] = None,
    vlnv: Annotated[Optional[str], Parameter(alias="-V")] = None,
    inference: Annotated[bool, Parameter(alias="-i")] = False,
    inference_interface: Annotated[Tuple[str, ...], Parameter(alias="-I")] = (),
    grouping_hint: Annotated[Tuple[str, ...], Parameter(alias="-g")] = (),
    lib: bool = False,
):
    """Package a single IP module parsed from its HDL sources into a Topwrap
    IP description YAML.

    ``SOURCES`` may interleave source files with ``+incdir+<dir>`` and
    ``+define+<name>[=<value>]`` arguments, the way other EDA tools accept
    them on their command line, e.g.::

        topwrap package top.sv +incdir+./inc +define+WIDTH=8

    Parameters
    ----------
    sources
        Source files to parse, optionally interleaved with ``+incdir+`` and
        ``+define+`` arguments.
    flist
        Filelist(s) to read further sources, ``+incdir+``/``+define+``
        arguments, and nested ``-f``/``-F <file>`` references from - the
        standard VCS/Verilator ``-f`` convention. Comments start with ``//``.
    output
        Where to write the IP description YAML. Defaults to
        ``<module-name>.yaml`` in the current directory.
    vlnv
        Override the packaged module's identifier, as
        ``vendor:library:name[:version]`` (version defaults to ``0.1`` if
        omitted). By default the name comes from the source and
        vendor/library/version are left at their generic defaults.
    inference
        Perform interface inference, matching the module's ports against
        known interface definitions (from registered libraries and Topwrap's
        built-ins) to group them into interfaces.
    inference_interface
        Restrict inference to these candidate interfaces, by name or their
        combined ``vendor_library_name_version`` identifier (repeatable).
        All known interfaces are considered when omitted.
    grouping_hint
        Hints for merging inferred candidate groups into one, as
        ``old1,old2,...,oldN=new`` (repeatable).
    lib
        Also write a CAPI2 ``.core`` file next to the IP description YAML,
        so the two together can be registered with ``topwrap library add``.
    """
    files, incdirs, defines = _collect_sources(sources, flist)
    if not files:
        logger.error("At least one source file must be provided")
        cli.help_print(["package"])
        sys.exit(1)

    repo_modules, _ = load_modules_from_repos()
    known_interfaces = list(load_interfaces_from_repos())

    frontend_output = SystemVerilogFrontend(
        modules=repo_modules, interfaces=known_interfaces
    ).parse_files(files, include_dirs=incdirs, defines=defines)

    if len(frontend_output.modules) == 0:
        logger.error("No module found in the given sources")
        sys.exit(1)
    if len(frontend_output.modules) > 1:
        names = ", ".join(sorted({m.id.name for m in frontend_output.modules}))
        logger.error(
            f"Found {len(frontend_output.modules)} modules in the given sources ({names}); "
            "'topwrap package' packages exactly one - narrow down the given sources"
        )
        sys.exit(1)

    module = frontend_output.modules[0]

    if inference:
        candidates = known_interfaces
        if inference_interface:
            candidates = [
                x
                for x in known_interfaces
                if x.id.name in inference_interface or x.id.combined() in inference_interface
            ]
        infer_interfaces_from_module(
            module, candidates, grouping_hints=parse_grouping_hints(grouping_hint)
        )

    if vlnv is not None:
        try:
            parsed = Identifier.parse_vlnv(vlnv)
        except ValueError:
            sys.exit(1)
        module.id = Identifier(
            name=parsed.name,
            vendor=parsed.vendor,
            library=parsed.library,
            version=parsed.version or "0.1",
        )

    existing_ifaces = {iface.id for iface in frontend_output.interfaces}
    backend = IpCoreDescriptionBackend(existing_ifaces)
    representation = backend.represent(module)
    module_yaml = next(backend.serialize(representation))

    out_path = output if output is not None else Path(f"{module.id.name}.yaml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(module_yaml.content)
    logger.info(f"Wrote {out_path}")

    if lib:
        core_path = out_path.parent / f"{module.id.name}.core"
        write_module_core(core_path, module.id, out_path, files)
        logger.info(f"Wrote {core_path}")
