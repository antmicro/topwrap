# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

from topwrap.backend.kpm.common import Positions
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier
from topwrap.model.module import Module


@dataclass
class OutputDir:
    target_dir: Path
    gensrc_dir: Path


@dataclass
class FileSource:
    path: Path


@dataclass
class StringSource:
    content: str


Source = Union[FileSource, StringSource]

#: Builds the module of an ``ips`` entry using ``generate``. Called with the instance name,
#: the entry's ``options`` and the directory of the design description that contains it.
IPGenerator = Callable[[str, dict[str, Any], Path], Module]


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

    #: List of identifiers of existing definitions in HDL code
    existing_interfaces: set[Identifier]

    #: IP generators provided by plugins, keyed on the provider name.
    ip_generators: dict[str, IPGenerator] = field(default_factory=dict)

    #: Additional VLNVs of cores the generated FuseSoC core depends on.
    fusesoc_dependencies: list[str] = field(default_factory=list)

    #: Map of generated outputs, keyed on the output stage name.
    outputs: dict[str, Any] = field(default_factory=dict)

    #: Map of module identifiers to the KPM position definitions.
    positions: dict[Identifier, Positions] = field(default_factory=dict)

    @property
    def all_modules(self) -> Iterable[Module]:
        return itertools.chain(self.repo_modules, self.loaded_modules)


class BuildException(Exception):
    pass


class ValidationException(BuildException):
    """The exception to be raised when a validation check fails."""

    pass


class PluginException(Exception):
    pass


class IPGeneratorException(BuildException):
    """Base of the errors related to IP generators."""


class IPGeneratorNotFoundException(IPGeneratorException):
    """A design uses a provider that no loaded plugin offers."""


class IPGeneratorConflictException(IPGeneratorException):
    """More than one plugin offers the same provider."""


class IPGeneratorOptionsException(IPGeneratorException):
    """Raised by a generator when its ``options`` are invalid."""


class IPGenerationException(IPGeneratorException):
    """Raised by a generator when generating the IP fails."""


class BasePlugin:
    #: Priority of the plugin. Hooks are invoked in order of decreasing priority.
    priority: int = 0

    def ip_generators(self) -> dict[str, IPGenerator]:
        """
        IP generators for ``generate`` entries in design descriptions, keyed on provider name.
        Generators report errors with :class:`IPGeneratorOptionsException` and
        :class:`IPGenerationException`.
        """
        return {}

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

    def pre_output_writing(self, ctx: BuildContext, target_dir: OutputDir):
        """Hook invoked before writing outputs to files."""
        pass

    def post_output_writing(self, ctx: BuildContext, target_dir: OutputDir):
        """Hook invoked after writing outputs to files."""
        pass
