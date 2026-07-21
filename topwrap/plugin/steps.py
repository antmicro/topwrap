# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import itertools
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, cast

from typing_extensions import override

from topwrap.backend.backend import BackendOutputInfo
from topwrap.backend.kpm.dataflow import KpmDataflowBackend
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.backend.yaml.backend import DesignDescriptionBackend
from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.fuse_helper import FuseSocBuilder
from topwrap.model.module import Module
from topwrap.plugin.base import (
    BuildContext,
    BuildException,
    FileSource,
    Source,
    StringSource,
)
from topwrap.util import JsonType, get_config

logger = logging.getLogger(__name__)


class InputStage(ABC):
    #: Name of the input stage.
    name: str

    @abstractmethod
    def process_input(
        self, design_source: Optional[Source], sources: list[Source], ctx: BuildContext
    ):
        """
        Process the given input file and add modules to the context.
        """
        ...

    def pre_parse_input(self, design_source: Optional[Source], sources: list[Source]):  # noqa: B027
        """
        Pre-Process the given input files. This is done before repo-discovery
        """
        pass


class Transformation(ABC):
    #: Name of the transformation.
    name: str

    #: Priority of the transformation. Transformations are applied in order of decreasing priority.
    priority: int

    #: Flag determining whether the transformation is only to be applied to modules which contain
    #: a design.
    design_only: bool

    @abstractmethod
    def apply_transformation(self, mod: Module, ctx: BuildContext):
        """
        Perform an in-place transformation on the module. In case the result of
        the transformation might be loaded again, care should be taken to make
        the transformations idempotent.
        """
        ...


class Validation(ABC):
    #: Name of the validation.
    name: str

    #: Priority of the validation. Validations are performed in order of decreasing priority.
    priority: int

    #: Flag determining whether the validation is only to be performed on modules which contain
    #: a design.
    design_only: bool

    @abstractmethod
    def validate(self, mod: Module, ctx: BuildContext):
        """
        Perform validation of a module.
        """
        ...


class OutputStage(ABC):
    #: Name of the output stage. Used as a key for the outputs in `BuildContext`.
    name: str

    def generate_output(self, ctx: BuildContext):  # noqa: B027
        """
        Generate some output and save it in the context.
        This method may be unimplemented if this stage does not save any intermediates.
        """
        pass

    @abstractmethod
    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        """
        Write out generated output to disk in the `target_dir` directory.
        """
        ...


class YamlInputStage(InputStage):
    name: str = "YAML"

    @override
    def process_input(
        self, design_source: Optional[Source], sources: list[Source], ctx: BuildContext
    ):
        frontend = YamlFrontend(ctx.all_modules, ctx.all_interfaces)

        if sources:
            for src in sources:
                if isinstance(src, FileSource):
                    frontend_output = frontend.parse_files([src.path])
                    ctx.loaded_modules += frontend_output.modules
                else:
                    assert isinstance(src, StringSource)
                    frontend_output = frontend.parse_str([src.content])
                    ctx.loaded_modules += frontend_output.modules

        if design_source:
            if isinstance(design_source, FileSource):
                frontend_output = frontend.parse_files([design_source.path])
            else:
                assert isinstance(design_source, StringSource)
                frontend_output = frontend.parse_str([design_source.content])

            ctx.top_module = frontend_output.modules[0]
            ctx.loaded_modules += [ctx.top_module]

            if ctx.top_module.design is None:
                raise BuildException(
                    f"Parsing design source {design_source} did not yield a design."
                )

    @override
    def pre_parse_input(self, design_source: Optional[Source], sources: list[Source]):
        from topwrap.frontend.yaml.design_schema import DesignDescription

        if design_source:
            if isinstance(design_source, FileSource):
                design = DesignDescription.load(design_source.path)
            else:
                assert isinstance(design_source, StringSource)
                design = DesignDescription.from_yaml(design_source.content)

            config_options = design.config
            if config_options:
                get_config().update_repo(config_options.repositories)
                get_config().update_interface_compliance(config_options.force_interface_compliance)


class KpmInputStage(InputStage):
    name: str = "KPM"

    @override
    def process_input(
        self, design_source: Optional[Source], sources: list[Source], ctx: BuildContext
    ):
        frontend = KpmFrontend(ctx.all_modules, ctx.all_interfaces)

        all_strings = all(isinstance(f, StringSource) for f in sources) and (
            design_source is None or isinstance(design_source, StringSource)
        )
        all_files = all(isinstance(f, FileSource) for f in sources) and (
            design_source is None or isinstance(design_source, FileSource)
        )

        if not all_strings and not all_files:
            raise BuildException("KPM input requires all sources be given as strings or files")

        if all_strings:
            strs = []
            if design_source:
                assert isinstance(design_source, StringSource)
                strs += [design_source.content]
            for s in sources:
                assert isinstance(s, StringSource)
                strs += [s.content]
            output = frontend.parse_str(strs)
        else:
            files = []
            if design_source:
                assert isinstance(design_source, FileSource)
                files += [design_source.path]
            for s in sources:
                assert isinstance(s, FileSource)
                files += [s.path]
            output = frontend.parse_files(files)

        ctx.loaded_modules += output.modules
        if design_source:
            ctx.top_module = frontend.get_top_design(output.modules).parent


class MemoryMapTransformation(Transformation):
    name: str = "Apply memory maps to interconnects"
    priority: int = 0
    design_only: bool = True

    @override
    def apply_transformation(self, mod: Module, ctx: BuildContext):
        assert mod.design is not None
        mod.design.update_interconnects_from_memory_maps()


class SystemVerilogOutputStage(OutputStage):
    name: str = "SystemVerilog module"

    @override
    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        if ctx.top_module is None:
            raise BuildException("SystemVerilog output requires a top module")

        backend = SystemVerilogBackend(ctx.repo_interfaces)
        repr = backend.represent(ctx.top_module)
        [out] = backend.serialize(repr, combine=True)

        out.save(target_dir)


class FuseSocOutputStage(OutputStage):
    name: str = "FuseSoC core"

    def __init__(self, part: Optional[str] = None, src_dirs: Optional[list[Path]] = None):
        self.part = part
        self.src_dirs = src_dirs if src_dirs is not None else []

    @override
    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        if ctx.top_module is None:
            raise BuildException("FuseSoC output requires a top module")

        if self.part is None:
            logging.warning(
                "You didn't specify the part number using the --part option. "
                "It will remain unspecified in the generated FuseSoC .core "
                "and your further implementation/synthesis may fail."
            )

        fuse_builder = FuseSocBuilder(self.part)

        fuse_builder.add_source(f"{ctx.top_module.id.name}.sv", "systemVerilogSource")
        fuse_builder.build(
            ctx.top_module.id.name,
            target_dir / f"{ctx.top_module.id.name}.core",
            sources_dir=self.src_dirs,
        )


class KpmSpecificationOutputStage(OutputStage):
    name: str = "KPM specification"

    def __init__(self, output_path: Optional[Path]):
        self.output_path = output_path

    @override
    def generate_output(self, ctx: BuildContext):
        spec = KpmSpecificationBackend.default()
        for module in itertools.chain(ctx.repo_modules, ctx.loaded_modules):
            try:
                spec.add_module(
                    module,
                    recursive=module is ctx.top_module,
                )
            except Exception as e:
                desc = "design " if module is ctx.top_module else ""
                raise BuildException(
                    f"An error occurred while generating specification for {desc}module "
                    f"'{module.id.name}' from '{module.refs[0].file}'"
                ) from e

        spec = spec.build()
        if ctx.top_module:
            assert ctx.top_module.design

            flow = KpmDataflowBackend(spec)
            flow.represent_design(ctx.top_module.design, depth=-1)
            spec = flow.apply_subgraphs_to_spec(spec)

        assert self.name not in ctx.outputs
        ctx.outputs[self.name] = spec

    @override
    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        assert self.name in ctx.outputs
        spec = cast(JsonType, ctx.outputs[self.name])

        if self.output_path:
            with open(self.output_path, "w") as f:
                f.write(json.dumps(spec))
        else:
            with open(target_dir / "kpm_spec.json", "w") as f:
                f.write(json.dumps(spec))


class KpmDataflowOutputStage(OutputStage):
    name: str = "KPM dataflow"

    def __init__(self, output_path: Optional[Path], *, specification: Optional[JsonType] = None):
        self.output_path = output_path
        self.specification = specification

    @override
    def generate_output(self, ctx: BuildContext):
        if ctx.top_module is None:
            raise BuildException("KPM dataflow output requires a top module")

        assert ctx.top_module.design

        if not self.specification:
            spec = KpmSpecificationBackend.default()
            for module in ctx.all_modules:
                try:
                    spec.add_module(
                        module,
                        recursive=module is ctx.top_module,
                    )
                except Exception as e:
                    desc = "design " if module is ctx.top_module else ""
                    raise BuildException(
                        f"An error occurred while generating specification for {desc}module "
                        f"'{module.id.name}' from '{module.refs[0].file}'"
                    ) from e

            self.specification = spec.build()

        flow = KpmDataflowBackend(self.specification)
        flow.represent_design(ctx.top_module.design, depth=-1)

        self.specification = flow.apply_subgraphs_to_spec(self.specification)

        flow = flow.build()

        assert self.name not in ctx.outputs
        ctx.outputs[self.name] = flow

    @override
    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        assert self.name in ctx.outputs
        flow = cast(JsonType, ctx.outputs[self.name])

        if self.output_path:
            with open(self.output_path, "w") as f:
                f.write(json.dumps(flow))
        else:
            with open(target_dir / "kpm_dataflow.json", "w") as f:
                f.write(json.dumps(flow))


class YamlDesignOutputStage(OutputStage):
    name: str = "Design YAML"

    @override
    def generate_output(self, ctx: BuildContext):
        if ctx.top_module is None:
            raise BuildException("Design YAML output requires a top module")

        assert ctx.top_module.design

        backend = DesignDescriptionBackend(ctx.all_interfaces)
        repr = backend.represent(ctx.top_module)

        assert self.name not in ctx.outputs
        ctx.outputs[self.name] = next(backend.serialize(repr))

    @override
    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        assert self.name in ctx.outputs
        out = cast(BackendOutputInfo, ctx.outputs[self.name])

        out.save(target_dir)
