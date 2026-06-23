# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module


@dataclass
class FileSource:
    path: Path


@dataclass
class StringSource:
    content: str


Source = Union[FileSource, StringSource]


@dataclass
class BuildContext:
    #: Modules loaded from repositories.
    repo_modules: list[Module]

    #: Interface definitions loaded from repositories.
    repo_interfaces: list[InterfaceDefinition]

    #: Path to the source file containing the design.
    design_source: Optional[Source]

    #: Paths to additional source files to be parsed.
    extra_sources: list[Source]

    #: Top-level module containing the design.
    top_module: Optional[Module]

    #: All loaded modules.
    loaded_modules: list[Module]

    #: All loaded interfaces.
    loaded_interfaces: list[InterfaceDefinition]

    #: Map of generated outputs, keyed on the output stage name.
    outputs: dict[str, Any] = field(default_factory=dict)

    @property
    def all_modules(self) -> Iterable[Module]:
        return itertools.chain(self.repo_modules, self.loaded_modules)

    @property
    def all_interfaces(self) -> Iterable[InterfaceDefinition]:
        return itertools.chain(self.repo_interfaces, self.loaded_interfaces)


class BuildException(Exception):
    pass


class PluginException(Exception):
    pass


class BasePlugin:
    #: Priority of the plugin. Hooks are invoked in order of decreasing priority.
    priority: int = 0

    def pre_ir_generation(self, ctx: BuildContext):
        """Hook invoked before parsing sources."""
        pass

    def post_ir_generation(self, ctx: BuildContext):
        """Hook invoked after parsing sources."""
        pass

    def pre_transform(self, ctx: BuildContext):
        """Hook invoked before applying transformations."""
        pass

    def post_transform(self, ctx: BuildContext):
        """Hook invoked after applying transformations."""
        pass

    def pre_validate(self, ctx: BuildContext):
        """Hook invoked before performing validation."""
        pass

    def post_validate(self, ctx: BuildContext):
        """Hook invoked after performing validation."""
        pass

    def pre_output_generation(self, ctx: BuildContext):
        """Hook invoked before generating outputs."""
        pass

    def post_output_generation(self, ctx: BuildContext):
        """Hook invoked after generating outputs (but before writing outputs to files)."""
        pass

    def pre_output_writing(self, ctx: BuildContext, target_dir: Path):
        """Hook invoked before writing outputs to files."""
        pass

    def post_output_writing(self, ctx: BuildContext, target_dir: Path):
        """Hook invoked after writing outputs to files."""
        pass
