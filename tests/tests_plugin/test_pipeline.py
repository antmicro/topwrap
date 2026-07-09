# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Optional, cast

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module
from topwrap.plugin.base import (
    BasePlugin,
    BuildContext,
    Source,
    StringSource,
)
from topwrap.plugin.manager import PluginManager
from topwrap.plugin.pipeline import BuildPipeline
from topwrap.plugin.steps import InputStage, OutputStage, Transformation, Validation


class MockPluginManager(PluginManager):
    def __init__(self, plugins: list[BasePlugin]):
        super().__init__()
        self.plugins = [(p.priority, type(p).__name__, p) for p in plugins]
        self.plugins = sorted(self.plugins, key=lambda x: x[0], reverse=True)
        self.loaded = True

    def load_plugins(self):
        pass


class MockInputStage(InputStage):
    name: str = "Mock input"

    def process_input(
        self, design_source: Optional[Source], sources: list[Source], ctx: BuildContext
    ):
        for s in sources:
            assert isinstance(s, StringSource)
            mod = Module(id=Identifier(s.content))
            ctx.loaded_modules += [Module(id=Identifier(s.content))]
        if design_source:
            assert isinstance(design_source, StringSource)
            mod = Module(id=Identifier(design_source.content))
            mod.design = Design()
            ctx.loaded_modules += [mod]
            ctx.top_module = mod


class MockTransformation(Transformation):
    name: str = "Mock transformation"

    def __init__(self, priority: int, design_only: bool, steps: list[str]):
        self.priority = priority
        self.design_only = design_only
        self.steps = steps

    def apply_transformation(self, mod: Module, ctx: BuildContext):
        self.steps += [f"transform {mod.id.name} {self.priority} {self.design_only}"]


class MockValidation(Validation):
    name: str = "Mock validation"

    def __init__(self, priority: int, design_only: bool, steps: list[str]):
        self.priority = priority
        self.design_only = design_only
        self.steps = steps

    def validate(self, mod: Module, ctx: BuildContext):
        self.steps += [f"validate {mod.id.name} {self.priority} {self.design_only}"]


class MockOutputStage(OutputStage):
    name: str = "Mock output stage"

    def __init__(self, parent_name: str, steps: list[str]):
        self.parent_name = parent_name
        self.steps = steps

    def generate_output(self, ctx: BuildContext):
        ctx.outputs[self.name + self.parent_name] = f"mock.{self.parent_name}.output"
        self.steps += [f"generate_output {self.parent_name}"]

    def write_output_to(self, target_dir: Path, ctx: BuildContext):
        assert (self.name + self.parent_name) in ctx.outputs
        out = cast(str, ctx.outputs[self.name + self.parent_name])

        with open(target_dir / out, "w") as f:
            f.write(out)
        self.steps += [f"write_output_to {target_dir / out} {self.parent_name}"]


class MockPlugin(BasePlugin):
    priority: int = 1

    def __init__(self, steps: list[str]):
        self.steps = steps

    def pre_ir_generation(self, ctx: BuildContext):
        self.steps += [f"pre_ir_generation {self.__class__.__name__}"]

    def post_ir_generation(self, ctx: BuildContext):
        self.steps += [f"post_ir_generation {self.__class__.__name__}"]

    def pre_transform(self, ctx: BuildContext):
        self.steps += [f"pre_transform {self.__class__.__name__}"]

    def post_transform(self, ctx: BuildContext):
        self.steps += [f"post_transform {self.__class__.__name__}"]

    def pre_validate(self, ctx: BuildContext):
        self.steps += [f"pre_validate {self.__class__.__name__}"]

    def post_validate(self, ctx: BuildContext):
        self.steps += [f"post_validate {self.__class__.__name__}"]

    def pre_output_generation(self, ctx: BuildContext):
        self.steps += [f"pre_output_generation {self.__class__.__name__}"]

    def post_output_generation(self, ctx: BuildContext):
        self.steps += [f"post_output_generation {self.__class__.__name__}"]

    def pre_output_writing(self, ctx: BuildContext, target_dir: Path):
        self.steps += [f"post_output_writing {self.__class__.__name__} {target_dir}"]

    def post_output_writing(self, ctx: BuildContext, target_dir: Path):
        self.steps += [f"post_output_writing {self.__class__.__name__} {target_dir}"]


class MockPluginHiPrio(MockPlugin):
    priority: int = 10


class TestBuildPipeline:
    @pytest.mark.usefixtures("fs")
    def test_blank_pipeline(self, fs: FakeFilesystem):
        steps: list[str] = []

        pipeline = BuildPipeline(
            inputs=[MockInputStage()],
            transformations=[
                MockTransformation(1, False, steps),
                MockTransformation(2, True, steps),
            ],
            validations=[MockValidation(1, False, steps), MockValidation(2, True, steps)],
            outputs=[MockOutputStage("A", steps), MockOutputStage("B", steps)],
            plugin_manager=MockPluginManager(
                [
                    MockPlugin(steps),
                    MockPluginHiPrio(steps),
                ]
            ),
        )

        outdir = fs.create_dir("output")
        pipeline.run_str(["a", "b", "c"], "d", Path(outdir.path))

        assert steps == [
            "pre_ir_generation MockPluginHiPrio",
            "pre_ir_generation MockPlugin",
            "post_ir_generation MockPluginHiPrio",
            "post_ir_generation MockPlugin",
            "pre_transform MockPluginHiPrio",
            "pre_transform MockPlugin",
            "transform d 2 True",
            "transform a 1 False",
            "transform b 1 False",
            "transform c 1 False",
            "transform d 1 False",
            "post_transform MockPluginHiPrio",
            "post_transform MockPlugin",
            "pre_validate MockPluginHiPrio",
            "pre_validate MockPlugin",
            "validate d 2 True",
            "validate a 1 False",
            "validate b 1 False",
            "validate c 1 False",
            "validate d 1 False",
            "post_validate MockPluginHiPrio",
            "post_validate MockPlugin",
            "pre_output_generation MockPluginHiPrio",
            "pre_output_generation MockPlugin",
            "generate_output A",
            "generate_output B",
            "post_output_generation MockPluginHiPrio",
            "post_output_generation MockPlugin",
            "post_output_writing MockPluginHiPrio /output",
            "post_output_writing MockPlugin /output",
            "write_output_to /output/mock.A.output A",
            "write_output_to /output/mock.B.output B",
            "post_output_writing MockPluginHiPrio /output",
            "post_output_writing MockPlugin /output",
        ]

        assert set(fs.listdir(outdir.path)) == {
            "mock.A.output",
            "mock.B.output",
        }
