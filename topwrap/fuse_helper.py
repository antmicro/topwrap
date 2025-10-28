# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from os import cpu_count, path
from pathlib import Path
from typing import Collection, Optional

from jinja2 import Environment, FileSystemLoader

from topwrap.util import path_relative_to

TEMPLATES_DIR = path.join(path.dirname(__file__), "templates")


class SourceFile:
    def __init__(self, filename, type):
        self.filename = filename
        self.type = type


class IP:
    def __init__(self, name, vlnv):
        """Create a new IP instance representation

        :param name: name of the instance
        :param vlnv: Version-Library-Name-Version string which represents
            specific IP Core implementation
        """
        self.name = name
        self.vlnv = vlnv


class FuseSocBuilder:
    """Use this class to generate a FuseSoC .core file"""

    def __init__(self, part):
        self.sources = []
        self.dependencies = []
        self.external_ips = []
        self.part = part

    def add_source(self, filename, type):
        """Adds an HDL source to the list of sources in the core file"""
        self.sources.append(SourceFile(filename, type))

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

    def add_dependency(self, dependency: str):
        """Adds a dependency to the list of dependencies in the core file"""
        self.dependencies.append(dependency)

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
        text = template.render(
            sources=self.sources,
            external_ips=self.external_ips,
            jobs=jobs,
            part=self.part,
            top_name=top_name,
        )
        with open(core_path, "w") as f:
            f.write(text)
