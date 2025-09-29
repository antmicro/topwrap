# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Callable, Optional, Union

import pytest

from examples.ir_examples.modules import ALL_MODULES, lfsr_gen
from topwrap.frontend.yaml.design import DesignDescriptionFrontend
from topwrap.frontend.yaml.design_schema import DesignDescription
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.frontend.yaml.ip_core import (
    InterfaceDescriptionFrontend,
    IPCoreDescriptionFrontend,
    _param_to_ir_param,
)
from topwrap.interface import get_interface_by_name
from topwrap.ip_desc import IPCoreComplexParameter
from topwrap.model.connections import PortDirection, ReferencedPort
from topwrap.model.design import Design
from topwrap.model.hdl_types import Bit, Bits
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import ElaboratableValue
from topwrap.model.module import Module
from topwrap.repo.user_repo import Core, UserRepo
from topwrap.resource_field import FileReferenceHandler
from topwrap.util import get_config

from .test_ir_examples import TestIrExamples


def _mkconn(
    des: Design,
    i1n: Optional[str],
    p1n: str,
    i2n: Optional[Union[str, ElaboratableValue]],
    p2n: str,
):
    const = isinstance(i2n, ElaboratableValue)
    i1 = None if i1n is None else des.components.find_by_name(i1n)
    i2 = None if i2n is None else des.components.find_by_name(i2n) if not const else i2n
    p1 = des.parent.ports.find_by_name(p1n) if i1 is None else i1.module.ports.find_by_name(p1n)
    p2 = (
        des.parent.ports.find_by_name(p2n)
        if i2 is None or const
        else i2.module.ports.find_by_name(p2n)
    )
    return (
        ReferencedPort(instance=i1, io=p1),
        ReferencedPort(instance=i2, io=p2) if not const else i2,
    )


class TestDesignDescriptionFrontend:
    @pytest.mark.parametrize(
        ["design", "validator"],
        [
            (Path("examples/ir_examples/simple/design.yaml"), TestIrExamples.ir_simple),
            (Path("examples/ir_examples/interface/design.yaml"), TestIrExamples.ir_interface),
            (Path("examples/ir_examples/hierarchical/design.yaml"), TestIrExamples.ir_hierarchy),
            (Path("examples/ir_examples/interconnect/design.yaml"), TestIrExamples.ir_interconnect),
        ],
    )
    def test_ir(self, design: Path, validator: Callable[[Module], None]):
        validator(DesignDescriptionFrontend(ALL_MODULES).parse_file(design).parent)

    def test_complex_yaml(self):
        front = DesignDescriptionFrontend()
        des = front.parse_file(Path("tests/data/data_kpm/conversions/complex/project_complex.yaml"))

        comps = ("s1_mod_3", "s1_mod_3_2", "s1_mod_3_3", "s2_mod_1", "s2_mod_2", "SUB")
        assert len(des.components) == len(comps)
        for comp in comps:
            assert des.components.find_by_name(comp) is not None

        assert des.parent.id.name == "top"
        assert len(des.parent.interfaces) == 0
        assert len(des.parent.parameters) == 0
        assert len(des.parent.ports) == 5

        ports = [
            (PortDirection.IN, "c_unt_in"),
            (PortDirection.IN, "cin"),
            (PortDirection.OUT, "cout"),
            (PortDirection.OUT, "cs_s1_f_int_out_2"),
            (PortDirection.INOUT, "legacy_external_type"),
        ]

        for dir, name in ports:
            p = des.parent.ports.find_by_name(name)
            assert p is not None and p.direction == dir

        params = [("s1_mod_3", 12), ("s1_mod_3_2", 11), ("s1_mod_3_3", 13)]

        for name, value in params:
            c = des.components.find_by_name(name)
            assert c is not None
            p = c.module.parameters.find_by_name("SUB_VALUE")
            assert p is not None and c.parameters[p._id].value == str(value)

        conns = [
            _mkconn(des, None, "c_unt_in", "SUB", "customized_ext_name_port"),
            _mkconn(des, None, "legacy_external_type", "SUB", "legacy_external_type"),
            _mkconn(des, None, "cs_s1_f_int_out_2", "s1_mod_3_3", "cs_s1_f_int_out_2"),
            _mkconn(des, "s1_mod_3", "cs_s1_mint_in_2", "s2_mod_1", "cs_s2_mint_out_2"),
            _mkconn(des, "s1_mod_3_2", "cs_s1_mint_in_2", "s1_mod_3", "cs_s1_f_int_out_2"),
            _mkconn(des, "s2_mod_1", "cs_s2_f_int_in_2", "s1_mod_3_2", "cs_s1_f_int_out_2"),
        ]

        for src, trg in conns:
            assert [*des.connections_with(src)] == [trg]

        hier = des.components.find_by_name("SUB").module.design
        assert hier is not None

        comps = ("SUB", "BETWEEN", "SUBEMPTY", "s1_mod_2", "s1_mod_2_2")
        assert len(hier.components) == len(comps)
        for comp in comps:
            assert hier.components.find_by_name(comp) is not None

        conns = [
            _mkconn(hier, None, "customized_ext_name_port", "SUB", "cs_s2_f_int_in_2"),
            _mkconn(hier, None, "legacy_external_type", "s1_mod_2", "cs_s1_mint_in_1"),
            _mkconn(hier, "SUB", "cs_s1_mint_in_2", "BETWEEN", "exposed"),
            _mkconn(hier, "s1_mod_2_2", "cs_s1_mint_in_1", "s1_mod_2", "cs_s1_f_int_out_1"),
        ]

        for src, trg in conns:
            assert [*hier.connections_with(src)] == [trg]

        betw = hier.components.find_by_name("BETWEEN").module.design

        assert betw is not None
        assert len(betw.components) == 1
        assert betw.components[0].name == "c_mod_2"

        conns = [
            _mkconn(betw, "c_mod_2", "c_int_out_2", None, "exposed"),
            _mkconn(betw, "c_mod_2", "c_mod_in_2", ElaboratableValue(666), ""),
        ]

        for src, trg in conns:
            assert [*betw.connections_with(src)] == [trg]

        assert (e := hier.components.find_by_name("SUBEMPTY").module.design) is not None
        assert e.components.find_by_name("SUBEMPTY") is not None

        assert (sub2 := hier.components.find_by_name("SUB").module.design) is not None

        conns = [
            _mkconn(sub2, "s1_mod_3_2", "cs_s1_mint_in_2", None, "cs_s1_mint_in_2"),
            _mkconn(sub2, "s1_mod_3_2", "cs_s1_mint_in_2", "s1_mod_3", "cs_s1_f_int_out_2"),
        ]

        assert [*sub2.connections_with(conns[0][0])] == [conns[1][1], conns[0][1]]

    def test_prefers_preloaded(self):
        des = Path("examples/ir_examples/simple/design.yaml")
        preloaded = DesignDescriptionFrontend([lfsr_gen]).parse_file(des)
        fresh = DesignDescriptionFrontend().parse_file(des)

        assert preloaded.components.find_by_name("gen1").module is lfsr_gen
        assert fresh.components.find_by_name("gen1").module is not lfsr_gen

    def test_repo_resource_interaction(self, tmpdir):
        """
        This is a test for a specific bug that occurred in the YAML design frontend
        when it couldn't match already parsed IR Modules from a repo passed in the
        constructor of the frontend with repo core resource references in the Design
        Description. This resulted in the parsed design using newly created IR Module
        instances for cores that were already loaded from the user repository previously.
        This is highly unwanted as all frontends should recognize modules received in
        the constructor amongst currently parsed sources and not create duplicate instances.
        """

        tmpdir = Path(tmpdir)

        (tmpdir / "core.v").write_text(r"module \321havefun$!!()*^ ; endmodule")

        repo = UserRepo("test")
        repo.add_resource(
            Core(
                "sanitized_name",
                top_level_name="321havefun$!!()*^",
                sources=[FileReferenceHandler(tmpdir / "core.v")],
            )
        )
        repo.save(tmpdir / "repo")

        DesignDescription.from_yaml(
            "{ips:{inst1:{file: &a 'repo[test]:sanitized_name'}, inst2:{file: *a}}}"
        ).save(tmpdir / "design.yaml")

        with pytest.MonkeyPatch.context() as ctx:
            ctx.setitem(get_config().repositories, "test", FileReferenceHandler(tmpdir / "repo"))
            try:
                del get_config().loaded_repos
            except AttributeError:
                pass
            mod = get_config().loaded_repos["test"].get_core_by_name("sanitized_name")
            assert mod is not None
            mod_from_repo = mod.ir_module.top_level
            des = DesignDescriptionFrontend([mod_from_repo]).parse_file(tmpdir / "design.yaml")
            mods_in_design = [c.module for c in des.components]
            assert len(mods_in_design) == 2 and all(m is mod_from_repo for m in mods_in_design)


class TestIPCoreDescriptionFrontend:
    def test_parse_on_mem_yaml(self):
        ip = Path("examples/ir_examples/interconnect/ips/mem.yaml")
        mod = IPCoreDescriptionFrontend().parse_file(ip)

        assert mod.id.name == "memory_block"

        assert len(mod.parameters) == 2
        assert (width := mod.parameters.find_by_name("WIDTH")) is not None
        assert (depth := mod.parameters.find_by_name("DEPTH")) is not None
        assert width.default_value == ElaboratableValue(32)
        assert depth.default_value == ElaboratableValue(0)

        assert len(mod.ports) == 11
        clk, rst = mod.non_intf_ports()
        assert isinstance(clk.type, Bit) and isinstance(rst.type, Bit)
        assert isinstance(idat := mod.ports.find_by_name("i_dat").type, Bits)
        assert idat.dimensions[0].upper == ElaboratableValue("WIDTH-1")

        [intf] = mod.interfaces
        assert intf.mode is InterfaceMode.SUBORDINATE
        assert intf.name == "bus"
        assert len(intf.signals) == 9
        assert all(s is not None for s in intf.signals.values())

    def test_complex_param(self):
        param = IPCoreComplexParameter(32, 563)
        assert _param_to_ir_param(param) == ElaboratableValue("32'd563")


class TestInterfaceDescriptionFrontend:
    def test_parse_wishbone(self):
        assert (old := get_interface_by_name("wishbone")) is not None
        idef = InterfaceDescriptionFrontend().parse(old)

        assert idef.id.name == "wishbone"
        assert len(idef.signals) == 18
        cyc = idef.signals.find_by_name("cyc")
        ack = idef.signals.find_by_name("ack")
        sel = idef.signals.find_by_name("sel")
        err = idef.signals.find_by_name("err")
        assert cyc.parent is idef
        assert cyc.regexp.search("wb_cyc")

        combs = [
            (cyc, True, PortDirection.OUT),
            (ack, True, PortDirection.IN),
            (sel, False, PortDirection.OUT),
            (err, False, PortDirection.IN),
        ]

        for sig, req, mstdir in combs:
            conf = sig.modes[InterfaceMode.MANAGER]
            assert conf.required == req and conf.direction == mstdir
            conf = sig.modes[InterfaceMode.SUBORDINATE]
            assert conf.required == req and conf.direction == mstdir.reverse()


class TestCombinedYamlFrontend:
    def test_combined(self):
        unrelated_ip = Path("examples/ir_examples/simple/ips/lfsr_gen.yaml")
        related_ip = Path("examples/ir_examples/interconnect/ips/mem.yaml")
        des = Path("examples/ir_examples/interconnect/design.yaml")

        mods = YamlFrontend().parse_files([unrelated_ip, des, related_ip]).modules
        assert len(mods) == 3
