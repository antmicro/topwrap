# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from typing import Callable, Iterable, Iterator

import pytest

from examples.ir_examples.modules import ALL_MODULES
from topwrap.backend.kpm.common import LayerType
from topwrap.frontend.kpm.common import KpmFrontendParseException
from topwrap.frontend.kpm.dataflow import KpmDataflowFrontend
from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.frontend.kpm.specification import KpmSpecificationFrontend
from topwrap.model.connections import PortDirection, ReferencedPort
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import ElaboratableValue
from topwrap.model.module import Module
from topwrap.util import JsonType

from .test_ir_examples import TestIrExamples


@pytest.fixture
def files() -> dict[str, JsonType]:
    files = {}
    for path in Path("tests/data/data_ir/frontend/kpm").glob("*.json"):
        with open(path) as f:
            files[path.stem] = json.load(f)
    return files


@pytest.fixture
def intf_defs() -> Iterable[InterfaceDefinition]:
    intfs: dict[str, InterfaceDefinition] = {}
    for mod in ALL_MODULES:
        for intf in mod.interfaces:
            intfs[intf.definition.id.combined()] = intf.definition
    return intfs.values()


class TestKpmSpecificationFrontend:
    @pytest.fixture
    def ip_cores(self, files: dict[str, JsonType]) -> list[JsonType]:
        return list(
            n for n in files["front_spec"]["nodes"] if n.get("layer", "") == LayerType.IP_CORE.value
        )

    def test_known_interfaces(
        self,
        files: dict[str, JsonType],
        ip_cores: list[JsonType],
        intf_defs: Iterator[InterfaceDefinition],
    ):
        front = KpmSpecificationFrontend([*intf_defs])
        mods = [*front.parse(files["front_spec"], allow_unknown_intfs=False)]
        assert len(mods) == len(ip_cores)

    def test_unknown_interfaces(self, files: dict[str, JsonType], ip_cores: list[JsonType]):
        front = KpmSpecificationFrontend()
        with pytest.raises(KpmFrontendParseException, match="no such interface"):
            mods = [*front.parse(files["front_spec"], allow_unknown_intfs=False)]
        mods = [*front.parse(files["front_spec"], allow_unknown_intfs=True)]
        assert len(mods) == len(ip_cores)

    def test_with_graph(
        self,
        files: dict[str, JsonType],
        ip_cores: list[JsonType],
        intf_defs: Iterator[InterfaceDefinition],
    ):
        spec, graph = files["front_spec"], files["interconnect_graph"]
        spec["graphs"] = [graph]

        front = KpmSpecificationFrontend([*intf_defs])
        mods: list[Module] = [*front.parse(spec, resolve_graphs=True)]
        assert len(mods) == len(ip_cores) + 1
        graph_mod = next(m for m in mods if m.id.name == "intr_top")
        assert len(graph_mod.design.interconnects) == 1


class TestKpmDataflowFrontend:
    @pytest.mark.parametrize(
        ["file", "validator"],
        [
            ("ir_simple_flow", TestIrExamples.ir_simple),
            ("ir_hier_flow", TestIrExamples.ir_hierarchy),
            ("ir_interface_flow", TestIrExamples.ir_interface),
            ("ir_interconn_flow", TestIrExamples.ir_interconnect),
        ],
    )
    def test_ir(self, files: dict[str, JsonType], file: str, validator: Callable[[Module], None]):
        front = KpmDataflowFrontend(ALL_MODULES)
        validator(front.parse(files[file]))

    def test_io_inference(self, files: dict[str, JsonType]):
        front = KpmDataflowFrontend(ALL_MODULES)
        mod = front.parse(files["io_inference_flow"])

        port = next(p for p in mod.ports if p.name == "test_port")
        intf = next(i for i in mod.interfaces if i.name == "test_intf")
        assert port.type == Bits(dimensions=[Dimensions(upper=ElaboratableValue("15"))])
        assert intf.definition.id.name == "wishbone"

    def test_complex(self, files: dict[str, JsonType]):
        front = KpmDataflowFrontend(ALL_MODULES)
        mod = front.parse(files["complex_flow"])
        assert mod.design is not None

        cout = next(p for p in mod.ports if p.name == "cout")
        assert cout.direction == PortDirection.OUT
        cout = ReferencedPort.external(cout)
        assert len([*mod.design.connections_with(cout)]) == 0

        debs = [c for c in mod.design.components if c.name == "debouncer"]
        graces = [
            d.parameters[next(p for p in d.module.parameters if p.name == "GRACE")._id].value
            for d in debs
        ]
        assert len(debs) == 2
        assert "99" in graces and "66" in graces

        soc = next(c for c in mod.design.components if c.name == "SOC")
        sub = next(c for c in mod.design.components if c.name == "SUB")
        assert soc.module.design is not None
        assert sub.module.design is not None

        legport = next(p for p in mod.ports if p.name == "in")
        legport = ReferencedPort.external(legport)
        [leg] = [*mod.design.connections_with(legport)]
        assert isinstance(leg, ReferencedPort)
        assert leg.instance == sub
        assert leg.io.name == "legacy_external_type"

        unluck = next(p for p in sub.module.ports if p.name == "unlucky_number")
        unluck = ReferencedPort.external(unluck)
        [elab] = [*sub.module.design.connections_with(unluck)]
        assert isinstance(elab, ElaboratableValue) and elab.value == "386"

        empty = next(c for c in sub.module.design.components if c.name == "SUBEMPTY")
        assert empty.module.design is not None
        subempty = next(c for c in empty.module.design.components if c.name == "SUBEMPTY")
        assert subempty.module.design is not None

        [uart] = mod.interfaces
        assert uart.definition.id.name == "wishbone"


class TestCombinedFrontend:
    @staticmethod
    def make_paths(*names: str) -> list[Path]:
        return [Path(f"tests/data/data_ir/frontend/kpm/{name}.json") for name in names]

    def test_all_mods(self, intf_defs: Iterator[InterfaceDefinition]):
        front = KpmFrontend(ALL_MODULES, [*intf_defs])
        mods = [*front.parse_files(self.make_paths("complex_flow", "ir_simple_flow"))]

        assert len(mods) == 2

    def test_no_mods_nor_spec(self, intf_defs: Iterator[InterfaceDefinition]):
        front = KpmFrontend(interfaces=[*intf_defs])

        with pytest.raises(ValueError, match="Illegal name"):
            [*front.parse_files(self.make_paths("complex_flow", "ir_simple_flow"))]

    def test_no_mods_spec(self, intf_defs: Iterator[InterfaceDefinition]):
        front = KpmFrontend(interfaces=[*intf_defs])
        mods = [*front.parse_files(self.make_paths("complex_flow", "ir_simple_flow", "front_spec"))]

        assert len(mods) == len(ALL_MODULES) + 3
