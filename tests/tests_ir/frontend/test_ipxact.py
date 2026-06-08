# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import glob
import re
from pathlib import Path
from typing import Optional

import pytest

from tests.tests_ir.frontend.test_ir_examples import TestIrExamples
from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.frontend.ipxact.frontend import IpXactFrontend
from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bit, Dimensions, LogicBitSelect
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module


@pytest.fixture
def ir_examples_path():
    return Path("examples/ir_examples/")


@pytest.fixture
def data_ir_ipxact_path():
    return Path("tests/data/data_ir/frontend/ipxact")


class TestIpxactIrExamples:
    def test_ir_example(self, ir_examples_path: Path):
        sources = [
            Path(name)
            for name in glob.glob(f"{ir_examples_path}/interface/ipxact/**/*.xml", recursive=True)
        ]
        frontend = IpXactFrontend()
        ir = frontend.parse_files(sources)
        top = None
        for module in ir.modules:
            if module.id.name == "top":
                top = module
                break
        assert top is not None
        assert top.id == Identifier(
            name="top", vendor="antmicro.com", library="interface", version="1.0"
        )
        TestIrExamples.ir_interface(top)

    def test_ir_hierarchical(self, ir_examples_path: Path):
        sources = [
            Path(name)
            for name in glob.glob(
                f"{ir_examples_path}/hierarchical/ipxact/**/*.xml", recursive=True
            )
        ]
        frontend = IpXactFrontend()
        ir = frontend.parse_files(sources)
        top = None
        for module in ir.modules:
            if module.id.name == "top":
                top = module
                break
        assert top is not None
        TestIrExamples.ir_hierarchy(top)

    def test_ir_interconnect(self, ir_examples_path: Path):
        sources = [
            Path(name)
            for name in glob.glob(
                f"{ir_examples_path}/interconnect/ipxact/**/*.xml", recursive=True
            )
        ]
        frontend = IpXactFrontend()
        ir = frontend.parse_files(sources)
        top: Optional[Module] = None
        for module in ir.modules:
            if module.id.name == "top":
                top = module
                break
        assert top is not None
        ext_manager_iface = top.interfaces.find_by_name("ext_manager")
        assert ext_manager_iface is not None
        des = top.design
        assert des is not None
        connection = des.connections.find_by(
            lambda iface: iface.source.io == ext_manager_iface
            or iface.target.io == ext_manager_iface
        )
        assert connection is not None
        if connection.target.io == ext_manager_iface:
            wb_manager_iface = connection.source
        else:
            wb_manager_iface = connection.target
        assert wb_manager_iface is not None
        assert wb_manager_iface.instance.name == "wishbone_interconnect1_0"
        assert wb_manager_iface.io.name == "manager1"
        assert len(des.components) == 4

        wb_iface = ext_manager_iface.definition
        assert len(wb_iface.signals) == 16
        tga_signal = wb_iface.signals.find_by_name("tga")
        assert tga_signal is not None
        assert tga_signal.modes[InterfaceMode.MANAGER].direction == PortDirection.OUT
        assert tga_signal.modes[InterfaceMode.SUBORDINATE].direction == PortDirection.OUT

        clk_signal = wb_iface.signals.find_by_name("clk")
        assert clk_signal is not None
        assert clk_signal.modes[InterfaceMode.UNSPECIFIED].direction == PortDirection.INOUT
        assert clk_signal.modes[InterfaceMode.MANAGER].direction == PortDirection.INOUT
        assert clk_signal.modes[InterfaceMode.SUBORDINATE].direction == PortDirection.INOUT

    def test_ir_simple(self, ir_examples_path: Path):
        sources = [
            Path(name)
            for name in glob.glob(f"{ir_examples_path}/simple/ipxact/**/*.xml", recursive=True)
        ]
        frontend = IpXactFrontend()
        ir = frontend.parse_files(sources)
        top: Optional[Module] = None
        for module in ir.modules:
            if module.id.name == "top":
                top = module
                break
        assert top is not None
        assert top.design is not None
        gen1 = top.design.components.find_by_name("gen1")
        assert gen1 is not None
        WIDTH = gen1.module.parameters.find_by_name("WIDTH")
        assert WIDTH is not None
        WIDTH_value = gen1.parameters[WIDTH._id]
        assert WIDTH_value.elaborate() == 128
        gen_out_port = gen1.module.ports.find_by_name("gen_out")
        assert gen_out_port is not None
        assert gen_out_port.direction is PortDirection.OUT
        assert gen_out_port.type.dimensions[0].upper.value == "WIDTH-1"
        assert gen_out_port.type.dimensions[0].lower.value == "0"

    def test_portmap_select_generation(self, data_ir_ipxact_path: Path):
        sources = [
            data_ir_ipxact_path / "portmap_cases.absDef.xml",
            data_ir_ipxact_path / "portmap_cases.xml",
        ]
        frontend = IpXactFrontend()
        ir = frontend.parse_files(sources)

        module = next(m for m in ir.modules if m.id.name == "portmap_comp")
        iface = module.interfaces.find_by_name_or_error("test_iface")
        idef = iface.definition

        def _ref(logical_name: str):
            sig_id = idef.signals.find_by_name_or_error(logical_name)._id
            return iface.signals[sig_id]

        hwrite = _ref("HWRITE")
        assert hwrite.select.ops == []

        tdata = _ref("TDATA")
        assert tdata.select.ops == []

        hburst = _ref("HBURST")
        assert hburst.select.ops == []

        myrange = _ref("MYRANGE")
        assert len(myrange.select.ops) == 1
        op = myrange.select.ops[0]
        assert isinstance(op, LogicBitSelect)
        assert op.slice == Dimensions(upper=ElaboratableValue(7), lower=ElaboratableValue(4))

        backend = IpCoreDescriptionBackend()
        out = backend.represent(module)
        [serialized] = backend.serialize(out)
        assert serialized.content

    def test_ir_interface_from_repo(self, ir_examples_path: Path):
        iface_path = ir_examples_path / "interface/ipxact/amba.com/AMBA4/axi4stream.xml"
        component_path = (
            ir_examples_path
            / "interface/ipxact/antmicro.com/interface/receiver/1.0/receiver.1.0.xml"
        )

        [iface_def] = IpXactFrontend().parse_files([iface_path]).interfaces

        frontend = IpXactFrontend(interfaces=[iface_def])
        ir = frontend.parse_files([component_path])

        receiver = next(m for m in ir.modules if m.id.name == "receiver")
        io_iface = receiver.interfaces.find_by_name("io")
        assert io_iface is not None
        assert io_iface.definition is iface_def
        assert io_iface.definition.id == Identifier(
            name="AXI 4 Stream", vendor="amba.com", library="AMBA4", version="r0p0_1"
        )

    def test_ir_interface_only_from_repo(self, ir_examples_path: Path):
        component_path = (
            ir_examples_path
            / "interface/ipxact/antmicro.com/interface/receiver/1.0/receiver.1.0.xml"
        )

        def _signal(name: str) -> InterfaceSignal:
            return InterfaceSignal(
                name=name,
                regexp=re.compile(name),
                type=Bit(),
                modes={
                    mode: InterfaceSignalConfiguration(PortDirection.INOUT, True)
                    for mode in InterfaceMode
                },
            )

        iface_def = InterfaceDefinition(
            id=Identifier(
                name="AXI 4 Stream", vendor="amba.com", library="AMBA4", version="r0p0_1"
            ),
            signals=[_signal(n) for n in ("TDATA", "TVALID", "TKEEP")],
        )

        frontend = IpXactFrontend(interfaces=[iface_def])
        ir = frontend.parse_files([component_path])

        receiver = next(m for m in ir.modules if m.id.name == "receiver")
        io_iface = receiver.interfaces.find_by_name("io")
        assert io_iface is not None
        assert io_iface.definition is iface_def
        assert io_iface.definition.signals.find_by_name("TDATA") is not None
