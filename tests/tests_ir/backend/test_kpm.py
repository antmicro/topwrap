# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pipeline_manager.dataflow_builder.entities import Direction

from examples.ir_examples.modules import (
    ALL_MODULES,
    axis_receiver,
    hier_top,
    intf_top,
    intr_top,
    simp_top,
)
from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.common import Metanode
from topwrap.backend.kpm.dataflow import KpmDataflowBackend
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.model.module import Design


class TestKpmSpecificationBackend:
    def test_empty(self):
        back = KpmSpecificationBackend()
        back.build()

    def test_default(self):
        back = KpmSpecificationBackend.default()
        out = back.build()

        assert len(out["nodes"]) == len(Metanode.__subclasses__())
        for meta in Metanode.__subclasses__():
            node = next(n for n in out["nodes"] if n["name"] == meta.name)
            for prop in meta("").properties:
                p = next(p for p in node["properties"] if p["name"] == prop.propname)
                assert p["type"] == prop.proptype
                assert p["default"] == prop.default
            for intf in meta("").interfaces:
                i = next(i for i in node["interfaces"] if intf.interfacename == i["name"])
                assert i["direction"] == intf.direction

    def test_modules(self):
        back = KpmSpecificationBackend.default()
        for mod in ALL_MODULES:
            back.add_module(mod)
        out = back.build()

        assert len(out["nodes"]) == len(ALL_MODULES) + len(Metanode.__subclasses__())

        receiver = next(n for n in out["nodes"] if n["name"] == "axis_receiver")
        io = next(i for i in receiver["interfaces"] if i["name"] == "io")
        assert io["direction"] == Direction.INPUT.value
        assert io["type"] == axis_receiver.interfaces[0].definition.id.combined()

    def test_recursive(self):
        back = KpmSpecificationBackend()
        back.add_module(simp_top, recursive=True)
        out = back.build()

        assert len(out["nodes"]) == 1 + 2

    def test_duplicates(self):
        back = KpmSpecificationBackend()
        back.add_module(simp_top)

        evil_mod = deepcopy(simp_top)
        # same name, different vendor
        evil_mod.id.vendor = "evil_vendor"

        back.add_module(evil_mod)
        out = back.build()

        assert len(out["nodes"]) == 2


class TestKpmDataflowBackend:
    @pytest.fixture
    def instance(self):
        back = KpmSpecificationBackend.default()
        for mod in ALL_MODULES:
            back.add_module(mod)
        out = back.build()
        return KpmDataflowBackend(out)

    @pytest.mark.parametrize(
        "top", [simp_top.design, intf_top.design, intr_top.design, hier_top.design]
    )
    def test_ir_examples(self, instance: KpmDataflowBackend, top: Design):
        instance.represent_design(top)
        instance.build()
        instance.represent_design(top, depth=-1)
        instance.build()


class TestCombined:
    @pytest.mark.parametrize("depth", [0, -1])
    def test_combined(self, depth: int):
        backend = KpmBackend(depth)

        with TemporaryDirectory() as tmpdir:
            for mod in (simp_top, intf_top, intr_top, hier_top):
                kpmout = backend.represent(mod)
                assert "nodes" in kpmout.specification
                assert "graphs" in kpmout.dataflow
                outs = backend.serialize(kpmout)
                for out in outs:
                    out.save(Path(tmpdir))

            assert len([*Path(tmpdir).iterdir()]) == 4 * 2
