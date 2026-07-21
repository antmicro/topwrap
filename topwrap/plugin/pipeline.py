# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Optional

from topwrap.cli import load_interfaces_from_repos, load_modules_from_repos
from topwrap.plugin.base import (
    BasePlugin,
    BuildContext,
    BuildException,
    FileSource,
    Source,
    StringSource,
)
from topwrap.plugin.manager import PluginManager
from topwrap.plugin.steps import (
    FuseSocOutputStage,
    InputStage,
    KpmDataflowOutputStage,
    KpmInputStage,
    KpmSpecificationOutputStage,
    MemoryMapTransformation,
    OutputStage,
    SystemVerilogOutputStage,
    Transformation,
    Validation,
    YamlDesignOutputStage,
    YamlInputStage,
)
from topwrap.util import JsonType

logger = logging.getLogger(__name__)


class BuildPipeline:
    inputs: list[InputStage]
    transformations: list[Transformation]
    validations: list[Validation]
    outputs: list[OutputStage]
    _ctx: Optional[BuildContext]

    def __init__(
        self,
        inputs: list[InputStage],
        transformations: list[Transformation],
        validations: list[Validation],
        outputs: list[OutputStage],
        *,
        plugin_manager: Optional[PluginManager] = None,
    ):
        self.plugin_manager = plugin_manager or PluginManager()
        self.plugin_manager.load_plugins()

        self.inputs = inputs
        self.transformations = sorted(transformations, key=lambda t: t.priority, reverse=True)
        self.validations = sorted(validations, key=lambda v: v.priority, reverse=True)
        self.outputs = outputs

        self._ctx = None

    @property
    def ctx(self) -> BuildContext:
        if not self._ctx:
            raise BuildException("prepare must be called before obtaining the context")
        return self._ctx

    def prepare(
        self,
        sources: list[Source],
        design_source: Optional[Source],
    ):
        logger.info("Preparing modules")

        # Pre-parse logic
        for i in self.inputs:
            logger.info(f"Pre-parsing design using: {i.name}")
            i.pre_parse_input(design_source, sources)

        repo_interfaces = load_interfaces_from_repos()
        repo_modules, existing_ifaces = load_modules_from_repos()

        self._ctx = BuildContext(
            repo_modules=[*repo_modules],
            repo_interfaces=existing_ifaces + [*repo_interfaces],
            design_source=design_source,
            extra_sources=sources,
            top_module=None,
            loaded_modules=[],
            loaded_interfaces=[],
        )

        self.plugin_manager.trigger(BasePlugin.pre_ir_generation, self.ctx)
        for i in self.inputs:
            logger.info(f"Processing inputs using: {i.name}")
            i.process_input(design_source, sources, self.ctx)
        self.plugin_manager.trigger(BasePlugin.post_ir_generation, self.ctx)

    def prepare_files(
        self,
        sources: list[Path],
        design_source: Optional[Path],
    ):
        self.prepare(
            [FileSource(f) for f in sources],
            design_source and FileSource(design_source),
        )

    def prepare_str(
        self,
        sources: list[str],
        design_source: Optional[str],
    ):
        self.prepare(
            [StringSource(f) for f in sources],
            StringSource(design_source) if design_source is not None else None,
        )

    def process(self):
        if not self.ctx:
            raise BuildException("prepare must be called before process")

        self.plugin_manager.trigger(BasePlugin.pre_transform, self.ctx)
        for t in self.transformations:
            for mod in self.ctx.loaded_modules:
                if t.design_only and mod.design is None:
                    continue
                logger.info(f"Running transformation: {t.name}")
                t.apply_transformation(mod, self.ctx)
        self.plugin_manager.trigger(BasePlugin.post_transform, self.ctx)

        self.plugin_manager.trigger(BasePlugin.pre_validate, self.ctx)
        for v in self.validations:
            for mod in self.ctx.loaded_modules:
                if v.design_only and mod.design is None:
                    continue
                logger.info(f"Running validation: {v.name}")
                v.validate(mod, self.ctx)
        self.plugin_manager.trigger(BasePlugin.post_validate, self.ctx)

        self.plugin_manager.trigger(BasePlugin.pre_output_generation, self.ctx)
        for o in self.outputs:
            logger.info(f"Generating output: {o.name}")
            o.generate_output(self.ctx)
        self.plugin_manager.trigger(BasePlugin.post_output_generation, self.ctx)

    def build(
        self,
        target_dir: Path,
    ):
        if not self.ctx:
            raise BuildException("prepare must be called before build")

        target_dir.mkdir(exist_ok=True)

        self.plugin_manager.trigger(BasePlugin.pre_output_writing, self.ctx, target_dir)
        for o in self.outputs:
            logger.info(f"Writing output: {o.name}")
            o.write_output_to(target_dir, self.ctx)
        self.plugin_manager.trigger(BasePlugin.post_output_writing, self.ctx, target_dir)

    def run(
        self,
        sources: list[Source],
        design_source: Optional[Source],
        target_dir: Path,
    ):
        self.prepare(sources, design_source)
        self.process()
        self.build(target_dir)

    def run_files(
        self,
        sources: list[Path],
        design_source: Optional[Path],
        target_dir: Path,
    ):
        self.run(
            [FileSource(f) for f in sources],
            design_source and FileSource(design_source),
            target_dir,
        )

    def run_str(
        self,
        sources: list[str],
        design_source: Optional[str],
        target_dir: Path,
    ):
        self.run(
            [StringSource(f) for f in sources],
            StringSource(design_source) if design_source is not None else None,
            target_dir,
        )

    @staticmethod
    def yaml_sv_pipeline(
        *,
        fuse: bool = False,
        fuse_part: Optional[str] = None,
        fuse_src_dirs: Optional[list[Path]] = None,
    ):
        outputs: list[OutputStage] = [SystemVerilogOutputStage()]
        if fuse:
            outputs += [FuseSocOutputStage(fuse_part, fuse_src_dirs)]

        return BuildPipeline(
            inputs=[
                YamlInputStage(),
            ],
            transformations=[
                MemoryMapTransformation(),
            ],
            validations=[],
            outputs=outputs,
        )

    @staticmethod
    def kpm_sv_pipeline(
        *,
        fuse: bool = False,
        fuse_part: Optional[str] = None,
        fuse_src_dirs: Optional[list[Path]] = None,
    ):
        outputs: list[OutputStage] = [SystemVerilogOutputStage()]
        if fuse:
            outputs += [FuseSocOutputStage(fuse_part, fuse_src_dirs)]

        return BuildPipeline(
            inputs=[
                KpmInputStage(),
            ],
            transformations=[
                MemoryMapTransformation(),
            ],
            validations=[],
            outputs=outputs,
        )

    @staticmethod
    def kpm_yaml_pipeline():
        return BuildPipeline(
            inputs=[
                KpmInputStage(),
            ],
            transformations=[
                MemoryMapTransformation(),
            ],
            validations=[],
            outputs=[
                YamlDesignOutputStage(),
            ],
        )

    @staticmethod
    def yaml_kpm_spec_pipeline(output_path: Optional[Path] = None):
        return BuildPipeline(
            inputs=[
                YamlInputStage(),
            ],
            transformations=[
                MemoryMapTransformation(),
            ],
            validations=[],
            outputs=[
                KpmSpecificationOutputStage(output_path),
            ],
        )

    @staticmethod
    def yaml_kpm_flow_pipeline(
        output_path: Optional[Path] = None, *, specification: Optional[JsonType] = None
    ):
        return BuildPipeline(
            inputs=[
                YamlInputStage(),
            ],
            transformations=[
                MemoryMapTransformation(),
            ],
            validations=[],
            outputs=[
                KpmDataflowOutputStage(output_path, specification=specification),
            ],
        )
