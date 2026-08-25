# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from itertools import product
from pathlib import Path
from typing import Callable, Optional, Union

import pytest

from examples.ir_examples.modules import ALL_MODULES, lfsr_gen
from topwrap.backend.kpm.common import Positions
from topwrap.backend.yaml.common.ip_core_schema import (
    IPCoreComplexParameter,
    IPCoreDescriptionFrontendException,
    param_to_ir_param,
)
from topwrap.frontend.yaml.design import DesignDescriptionFrontend, DesignPositionsFrontend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.model.connections import PortDirection, ReferencedPort
from topwrap.model.design import Design
from topwrap.model.hdl_types import Bit, Bits, BitStruct, Dimensions, LogicArray
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module
from topwrap.repo.user_repo import InterfaceDefinitionResource
from topwrap.resource_field import (
    FileReferenceHandler,
    GitReferenceHandler,
    RepoReferenceHandler,
    ResourceReferenceHandler,
    UriReferenceHandler,
    YamlCommonSchemes,
)
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
            (Path("examples/ir_examples/inverted/design.yaml"), TestIrExamples.ir_inverted),
            (Path("examples/ir_examples/clocks/design.yaml"), TestIrExamples.ir_clocks),
        ],
    )
    def test_ir(self, design: Path, validator: Callable[[Module], None]):
        design_ir, _ = DesignDescriptionFrontend(ALL_MODULES).parse_file(design)
        design_ir.update_interconnects_from_memory_maps()
        validator(design_ir.parent)

    def test_complex_yaml(self):
        front = DesignDescriptionFrontend()
        des, _ = front.parse_file(
            Path("tests/data/data_kpm/conversions/complex/project_complex.yaml")
        )
        des.update_interconnects_from_memory_maps()

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
        preloaded, _ = DesignDescriptionFrontend([lfsr_gen]).parse_file(des)
        fresh, _ = DesignDescriptionFrontend().parse_file(des)

        assert preloaded.components.find_by_name("gen1").module is lfsr_gen
        assert fresh.components.find_by_name("gen1").module is not lfsr_gen

    def test_extensions(self):
        des = """
        name: design
        extensions:
            key0: 123
            key1: text
            key2: [1, 2, 3]
            key3:
                subkey1: 123
        """

        mod, _ = DesignDescriptionFrontend().parse_str(des)
        exts = list(mod.extensions)

        assert len(exts) == 4
        assert exts[0].name == "key0"
        assert exts[0].data == 123

        assert exts[1].name == "key1"
        assert exts[1].data == "text"

        assert exts[2].name == "key2"
        assert exts[2].data == [1, 2, 3]

        assert exts[3].name == "key3"
        assert exts[3].data == {"subkey1": 123}

    def test_config_field(self):
        no_config = """
            name: top
        """
        sep = "\n                    "
        config_repo_template = """
            name: top
            config:
                {rep}
                {fic}
        """
        force_interface_compliance = [None, True, False]

        repositories: list[dict[str, ResourceReferenceHandler]] = [
            {},
            {"a": RepoReferenceHandler("abc", ["def"])},
            {"a": UriReferenceHandler("abc", ["def"])},
            {"a": GitReferenceHandler("abc", ["def"])},
            {"a": FileReferenceHandler("abc", ["def"])},
        ]
        required_handlers = YamlCommonSchemes.handlers
        assert all(
            any(isinstance(h, req_h) for r in repositories for h in r.values())
            for req_h in required_handlers
        ), "test_config_output does not cover all reference handlers"

        for fic, rep in product(force_interface_compliance, repositories):
            front = DesignDescriptionFrontend()
            if fic is None and not rep:
                source_yaml = no_config
                out, _ = front.parse_str(source_yaml)
                assert out.config is None
            else:
                repo_source = ""
                if rep:
                    repo_source = (
                        "repositories:"
                        + sep
                        + "   "
                        + (sep + "    ").join(f"{name}: {h.to_str()}" for name, h in rep.items())
                    )

                fic_source = ""
                if fic is not None:
                    fic_source = f"force_interface_compliance: {fic}"

                source_yaml = config_repo_template.format(fic=fic_source, rep=repo_source)
                print(source_yaml)
                out, _ = front.parse_str(source_yaml)

                assert out.config is not None
                assert out.config.force_interface_compliance == (False if fic is None else fic)

                assert set(out.config.repositories) == set(rep.keys())
                keys = rep.keys()
                assert all(type(out.config.repositories[k]) is type(rep[k]) for k in keys)
                assert all(out.config.repositories[k].to_str() == rep[k].to_str() for k in keys)


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

    def test_extensions(self):
        des = """
        id:
          name: top
          vendor: vendor
          library: libdefault
        extensions:
            key0: 123
            key1: text
            key2: [1, 2, 3]
            key3:
                subkey1: 123
        """

        mod = IPCoreDescriptionFrontend().parse_str(des)
        exts = list(mod.extensions)

        assert len(exts) == 4
        assert exts[0].name == "key0"
        assert exts[0].data == 123

        assert exts[1].name == "key1"
        assert exts[1].data == "text"

        assert exts[2].name == "key2"
        assert exts[2].data == [1, 2, 3]

        assert exts[3].name == "key3"
        assert exts[3].data == {"subkey1": 123}

    def test_complex_param(self):
        param = IPCoreComplexParameter(32, 563)
        assert param_to_ir_param(param) == ElaboratableValue(IPCoreComplexParameter(32, 563))

    def test_complex_signal(self):
        ip = """
        id:
          name: top
          vendor: vendor
          library: libdefault
        signals:
          in:
            - name: foo
              bound: [7, 0]
              default: 4
            - ["bar", 7, 0]
        """

        mod = IPCoreDescriptionFrontend().parse_str(ip)

        assert mod.id.name == "top"

        assert len(mod.ports) == 2
        foo = mod.ports.find_by_name_or_error("foo")
        bar = mod.ports.find_by_name_or_error("bar")

        assert foo.direction == PortDirection.IN
        assert bar.direction == PortDirection.IN

        ty = Bits(dimensions=[Dimensions(upper=ElaboratableValue(7))])

        assert foo.type == ty
        assert bar.type == ty

        assert foo.default_value == ElaboratableValue("4")
        assert bar.default_value is None

    def test_bad_intf_clock(self):
        ip = """
        id:
          library: libdefault
          vendor: vendor
          name: top
        interfaces:
          foo:
            type:
                name: wishbone
            mode: manager
            clock: asdf
        """

        with pytest.raises(IPCoreDescriptionFrontendException, match="use non-existent clock"):
            IPCoreDescriptionFrontend().parse_str(ip)

    def test_bad_intf_reset(self):
        ip = """
        id:
          library: libdefault
          vendor: vendor
          name: top
        interfaces:
          foo:
            type:
                name: wishbone
                vendor: vendor
                library: libdefault
            mode: manager
            reset: asdf
        """

        with pytest.raises(IPCoreDescriptionFrontendException, match="use non-existent reset"):
            IPCoreDescriptionFrontend().parse_str(ip)

    def test_typed_port(self):
        ip = """
        id:
          library: libdefault
          vendor: vendor
          name: top
        types:
          some_type:
            members:
              - name: some_bits
                type: [1, 0]
        signals:
          in:
            - {name: foo, type: some_type}
        """

        mod = IPCoreDescriptionFrontend().parse_str(ip)
        foo = mod.ports.find_by_name_or_error("foo")
        some_type = foo.type

        assert isinstance(some_type, BitStruct)
        assert some_type.name == "some_type"
        assert len(some_type.fields) == 1

        fld = some_type.fields[0]
        assert fld.field_name == "some_bits"
        assert isinstance(fld.type, LogicArray)
        assert isinstance(fld.type.item, Bit)
        assert fld.type.dimensions == [
            Dimensions(upper=ElaboratableValue(1), lower=ElaboratableValue(0))
        ]

    def test_bad_port_type(self):
        ip = """
        id:
          library: libdefault
          vendor: vendor
          name: top
        signals:
          in:
            - {name: foo, type: some_type}
        """

        with pytest.raises(IPCoreDescriptionFrontendException, match="references unknown type"):
            IPCoreDescriptionFrontend().parse_str(ip)

    def test_intf_signal_path(self):
        ip = """
        id:
          library: libdefault
          vendor: vendor
          name: top
        interfaces:
          foo:
            type:
              name: wishbone
            mode: manager
            signals:
              in:
                ack: {path: wb_resp_port.foo.ack}
        types:
          wb_resp_t:
            members:
              - name: foo
                type:
                  members:
                    - name: ack
                      type: [0, 0]
        signals:
          in:
            - {name: wb_resp_port, type: wb_resp_t}
        """

        mod = IPCoreDescriptionFrontend().parse_str(ip)

        wb_resp_port = mod.ports.find_by_name_or_error("wb_resp_port")
        type_outer = wb_resp_port.type

        assert isinstance(type_outer, BitStruct)
        assert type_outer.name == "wb_resp_t"
        assert len(type_outer.fields) == 1

        fld_outer = type_outer.fields[0]
        assert fld_outer.field_name == "foo"
        type_inner = fld_outer.type

        assert isinstance(type_inner, BitStruct)
        assert type_inner.name is None
        assert len(type_inner.fields) == 1

        fld_inner = type_inner.fields[0]
        assert fld_inner.field_name == "ack"

    def test_bad_intf_signal_path(self):
        ip = """
        id:
          library: libdefault
          vendor: vendor
          name: top
        interfaces:
          foo:
            type:
              name: wishbone
            mode: manager
            signals:
              in:
                ack: {path: wb_resp_port.foo.missing}
        types:
          wb_resp_t:
            members:
              - name: foo
                type:
                  members:
                    - name: ack
                      type: [0, 0]
        signals:
          in:
            - {name: wb_resp_port, type: wb_resp_t}
        """

        with pytest.raises(ValueError, match="is not a member of struct"):
            IPCoreDescriptionFrontend().parse_str(ip)

    def test_parse_vendor_field(self):
        vendor_name = "antmicro"
        YAML = f"""
        name: test_design
        vendor: {vendor_name}

        external:
            ports:
                out:
                    - PORT_OUT
        """

        frontend = YamlFrontend()
        res = frontend.parse_str([YAML]).modules[0]
        assert res.id.vendor == vendor_name

    def test_parse_library_field(self):
        library_name = "default"
        YAML = f"""
        name: test_design
        library: {library_name}

        external:
            ports:
                out:
                    - PORT_OUT
        """

        frontend = YamlFrontend()
        res = frontend.parse_str([YAML]).modules[0]
        assert res.id.library == library_name

    def test_parse_vendor_and_library_field(self):
        vendor_name = "antmicro"
        library_name = "default"
        YAML = f"""
        name: foo
        vendor: {vendor_name}
        library: {library_name}

        external:
            ports:
                out:
                    - PORT_OUT
        """

        frontend = YamlFrontend()
        res = frontend.parse_str([YAML]).modules[0]
        assert res.id.vendor == vendor_name
        assert res.id.library == library_name


class TestInterfaceDescriptionFrontend:
    def test_parse_wishbone(self):
        old = None
        for resource in get_config().builtin_repo.get_resources(InterfaceDefinitionResource):
            if resource.name == "vendor_libdefault_wishbone_0.1":
                old = resource
        assert old is not None
        idef = old.definition

        assert idef.id.name == "wishbone"
        assert len(idef.signals) == 18
        cyc = idef.signals.find_by_name("cyc")
        assert cyc is not None
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

    def test_existing_name_conflict(self):
        existing_mod = Module(id=Identifier(name="memory_block"))
        front = YamlFrontend(modules=[existing_mod])

        path_to_yaml = Path("examples/ir_examples/interconnect/ips/mem.yaml")

        out = front.parse_files([path_to_yaml])
        assert len(out.modules) == 1
        assert out.modules[0].id.name == "memory_block"


class TestDesignPositionsFrontend:
    def test_positions(self):
        src = """
modules:
- id:
    library: libdefault
    name: foo
    vendor: vendor
    version: '0.1'
  components:
  - name: comp1
    position: [123.0, 456.0]
  - name: comp2
    position: [21.0, 54.0]
  inverters:
  - position: [22.0, 33.0]
    source: inp
    target: [comp1, outp]
- id:
    library: libdefault
    name: bar
    vendor: vendor
    version: '0.1'
  clock_domains:
  - name: default
    position: [9.0, 3.0]
  constants:
  - name: '0'
    position: [5.0, 4.0]
  externals:
  - name: a
    position: [1.0, 2.0]
  identifier: [-1.0, -1.0]
  interconnects:
  - name: intercon1
    position: [10.0, 7.0]
  reset_domains:
  - name: default
    position: [9.0, 5.0]
"""

        frontend = DesignPositionsFrontend()
        pos = frontend.parse_str(src)

        assert pos == {
            Identifier("foo"): Positions(
                components={"comp1": (123, 456), "comp2": (21, 54)},
                inverters={((None, "inp"), ("comp1", "outp")): (22, 33)},
            ),
            Identifier("bar"): Positions(
                externals={"a": (1, 2)},
                constants={"0": (5, 4)},
                clock_domains={"default": (9, 3)},
                reset_domains={"default": (9, 5)},
                interconnects={"intercon1": (10, 7)},
                identifier=(-1, -1),
            ),
        }
