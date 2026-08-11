# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import logging
from dataclasses import dataclass
from os import cpu_count, path
from pathlib import Path
from re import compile
from typing import Collection, Optional, Union

from jinja2 import Environment, FileSystemLoader

from topwrap.util import path_relative_to

TEMPLATES_DIR = path.join(path.dirname(__file__), "templates")

logger = logging.getLogger(__name__)


class SourceFile:
    def __init__(self, filename: Path, type: str):
        self.filename = filename
        self.type = type


# FIXME: this should probably be more centralized
# FIXME: this is **very** permissive
VLNV_RE = compile(r"^([^:]*):([^:]*):([^:]*)(?::([^:]*))?$")


@dataclass
class FileSetDependency:
    vendor: str
    library: str
    name: str
    version: str

    @staticmethod
    def parse_vlnv(src: str) -> "FileSetDependency":
        m = VLNV_RE.fullmatch(src)

        if not m:
            _s = f"Failed to parse VLNV: {src}"
            logger.error(_s)
            # FIXME: a proper error type here
            raise AssertionError(_s)

        return FileSetDependency(m[1], m[2], m[3], m[4])


class IP:
    def __init__(self, name: str, vlnv: str):
        """Create a new IP instance representation

        :param name: name of the instance
        :param vlnv: Version-Library-Name-Version string which represents
            specific IP Core implementation
        """
        self.name = name
        self.vlnv = vlnv


@dataclass
class FuseSocHook:
    type: str
    scripts: list[str]


SUPPORTED_FUSESOC_TOOLS = frozenset(["vivado", "verilator"])
SUPPORTED_FUSESOC_FLOWS = frozenset(["sim"])
SUPPORTED_FUSESOC_FLOW_TOOLS = frozenset(["verilator"])


class FuseSocFlow:
    type = "unknown"
    tool = "unknown"

    def __init__(self, make_options: Optional[list[str]] = None):
        self.make_options = [] if make_options is None else make_options

    def is_valid(self) -> bool:
        return self.type in SUPPORTED_FUSESOC_FLOWS and self.tool in SUPPORTED_FUSESOC_FLOW_TOOLS


class FuseSocFlowVerilator(FuseSocFlow):
    type = "sim"
    tool = "verilator"


class FuseSocTool:
    """Base class for tool settings in fusesoc target"""

    type = "unknown"

    def is_valid(self) -> bool:
        return self.type in SUPPORTED_FUSESOC_TOOLS


class FuseSocToolVivado(FuseSocTool):
    type = "vivado"

    def __init__(self, part: str | None):
        self.part = part


class FuseSocToolVerilator(FuseSocTool):
    type = "verilator"


class FuseSocToolAPI:
    def __init__(self, default_tool: str, tools: Optional[list[FuseSocTool]]):
        self.default_tool = str
        self.tools = [] if tools is None else tools

        if not any(default_tool == tool.type for tool in self.tools):
            _s = "The default tool does not exist in the list of tools"
            logger.error(_s)
            raise AssertionError(_s)  # FIXME: what's the proper error?


class FuseSocTarget:
    def __init__(
        self,
        name: str,
        toplevel: str,
        api: Union[FuseSocToolAPI, FuseSocFlow],
        /,
        filesets: Optional[list[str]] = None,
        hooks: Optional[list[FuseSocHook]] = None,
    ):
        self.name = name
        self.toplevel = toplevel
        self.filesets = filesets or []
        self.hooks = hooks or []
        self.flow = api if isinstance(api, FuseSocFlow) else None
        self.tool = api if isinstance(api, FuseSocToolAPI) else None
        self.is_flow = isinstance(api, FuseSocFlow)


@dataclass
class FuseSocFileSet:
    label: str
    sources: list[SourceFile]
    depends: list[FileSetDependency]


@dataclass
class FuseSocScript:
    label: str
    args: list[str]

    def __post_init__(self):
        # Add necessary string
        for i in range(len(self.args)):
            arg = self.args[i]

            if arg.startswith("'"):
                continue

            if " " in arg:
                self.args[i] = f"'\"{arg}\"'"


class FuseSocBuilder:
    """Use this class to generate a FuseSoc .core file"""

    def __init__(self, part: Optional[str]):
        self.sources = []
        self.dependencies = []
        self.external_ips = []
        self.part = part
        self.targets: list[FuseSocTarget] = []
        self.scripts: list[FuseSocScript] = []
        self.filesets: list[FuseSocFileSet] = []
        self._generate_default_vivado = True

    def set_generate_vivado(self, generate_vivado: bool):
        self._generate_default_vivado = generate_vivado

    def add_source(self, filename: Path, type: str):
        """Adds an HDL source to the list of sources in the core file"""
        self.sources.append(SourceFile(filename, type))

    def add_target(self, target: FuseSocTarget):
        """Add a named fusesoc target"""
        self.targets.append(target)

    def add_script(self, script: FuseSocScript):
        """Add a named fusesoc script"""
        self.scripts.append(script)

    def add_fileset(self, fileset: FuseSocFileSet):
        """Add a complete fileset to the core file"""
        self.filesets.append(fileset)

    def add_sources_dir(self, sources_dir: Collection[Path], core_path: Path):
        """Given a name of a directory, add all files found inside it.
        Recognize VHDL, Verilog, and XDC files.
        """
        for dir in sources_dir:
            for f in dir.glob("**/*"):
                suf = f.suffix.lower()
                if suf in [".vhd", ".vhdl"]:
                    f_type = "vhdlSource"
                elif suf == ".v":
                    f_type = "verilogSource"
                elif suf == ".sv":
                    f_type = "systemVerilogSource"
                elif suf == ".xdc":
                    f_type = "xdc"
                else:
                    continue

                self.add_source(path_relative_to(f, core_path.parent), f_type)

    def add_dependency(self, dependency: str | FileSetDependency):
        """Adds a dependency to the list of dependencies in the core file"""
        if isinstance(dependency, FileSetDependency):
            self.dependencies.append(dependency)
        else:
            vlnv_parsed = FileSetDependency.parse_vlnv(dependency)
            self.dependencies.append(vlnv_parsed)

    def add_external_ip(self, vlnv: str, name: str):
        """Store information about IP Cores from Vivado library
        to generate hooks that will add the IPs in a TCL script.
        """
        self.external_ips.append(IP(name, vlnv))

    def build(
        self,
        top_name: str,
        core_path: Path,
        sources_dir: Collection[Path] = [],
        template_name: Optional[str] = None,
    ):
        """Generate the final create .core file

        :param sources_dir: additional directory with source files to add
        :param template_name: name of jinja2 template to be used,
            either in working directory, or bundled with the package.
            defaults to a bundled template
        """
        if sources_dir:
            self.add_sources_dir(sources_dir, core_path)
        if template_name is None:
            template_name = "core.yaml.j2"
        env = Environment(
            loader=FileSystemLoader(searchpath=["./", TEMPLATES_DIR]),
        )
        template = env.get_template(template_name)
        jobs = cpu_count() or 4

        # Generate the default rtl set
        self.filesets.append(
            FuseSocFileSet(
                label="rtl",
                sources=self.sources,
                depends=self.dependencies,
            )
        )

        if self._generate_default_vivado:
            self.targets.append(
                FuseSocTarget(
                    "default",
                    "top_name",
                    FuseSocToolAPI(default_tool="vivado", tools=[FuseSocToolVivado(self.part)]),
                    filesets=["rtl"],
                    hooks=[FuseSocHook("pre_build", ["set_jobs"])],
                )
            )

            self.scripts.append(
                FuseSocScript(
                    "set_jobs",
                    [
                        "sed",
                        "-i",
                        f"s/launch_runs synth_1/launch_runs synth_1 -jobs {jobs}/g",
                        f"{top_name}_0_synth.tcl",
                    ],
                )
            )

        text = template.render(
            top_name=top_name,
            filesets=self.filesets,
            targets=self.targets,
            scripts=self.scripts,
        )
        with open(core_path, "w") as f:
            f.write(text)
