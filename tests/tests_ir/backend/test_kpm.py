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
from topwrap.model.connections import ConstantConnection, Port, PortDirection, ReferencedPort
from topwrap.model.design import ModuleInstance
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Design, Module


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
        evil_mod.id = Identifier(vendor="evil_vendor", name=evil_mod.id.name)

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

    def test_constants_dedup(self, instance: KpmDataflowBackend):
        bbox_exts = [
            Port(name="in1", direction=PortDirection.IN),
            Port(name="in2", direction=PortDirection.IN),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )
        bbox_inst = ModuleInstance(name="bbox", module=bbox)

        sub_exts = [
            Port(name="in1", direction=PortDirection.IN),
            Port(name="in2", direction=PortDirection.IN),
        ]
        sub = Module(
            id=Identifier(name="sub"),
            ports=sub_exts,
            design=Design(
                components=[bbox_inst],
                connections=[
                    ConstantConnection(
                        source=ElaboratableValue("0"),
                        target=ReferencedPort(instance=bbox_inst, io=bbox_exts[0]),
                    ),
                    ConstantConnection(
                        source=ElaboratableValue("0"),
                        target=ReferencedPort(instance=bbox_inst, io=bbox_exts[1]),
                    ),
                ],
            ),
        )
        sub_inst = ModuleInstance(name="sub", module=sub)

        top = Module(
            id=Identifier(name="top"),
            ports=[],
            design=Design(
                components=[sub_inst],
                connections=[
                    ConstantConnection(
                        source=ElaboratableValue("0"),
                        target=ReferencedPort(instance=sub_inst, io=sub_exts[0]),
                    ),
                    ConstantConnection(
                        source=ElaboratableValue("0"),
                        target=ReferencedPort(instance=sub_inst, io=sub_exts[1]),
                    ),
                ],
            ),
        )

        assert top.design
        instance.represent_design(top.design, depth=-1)
        flow = instance.build()

        top_graph = flow["graphs"][0]
        sub_graph = flow["graphs"][1]

        # Make sure there aren't any extra nodes (=> extra constants)

        # Identifier + Constant + sub
        assert len(top_graph["nodes"]) == 3

        # Identifier + Constant + 2x External I/O + bbox
        assert len(sub_graph["nodes"]) == 5


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
