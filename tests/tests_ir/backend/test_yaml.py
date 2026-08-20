# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import copy
from itertools import product
from pathlib import Path

import pytest
import yaml
from typing_extensions import Optional

from examples.ir_examples.modules import (
    adv_top,
    hier_top,
    intf_top,
    intr_top,
    simp_top,
)
from tests.tests_ir.test_kpm_non_destructive import _compare_designs, _compare_modules
from topwrap import util
from topwrap.backend.kpm.common import Positions
from topwrap.backend.yaml.backend import (
    DesignDescriptionBackend,
    DesignPositionsBackend,
    IpCoreDescriptionBackend,
)
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.yaml.design import DesignDescriptionFrontend
from topwrap.frontend.yaml.ip_core import IPCoreDescriptionFrontend
from topwrap.interconnects.wishbone_rr import (
    WishboneInterconnect,
    WishboneRRManagerParams,
    WishboneRRParams,
    WishboneRRSubordinateParams,
)
from topwrap.model.config import ConfigDescription
from topwrap.model.connections import (
    Clock,
    Port,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
    Reset,
    ResetPolarity,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    LogicArray,
    LogicBitSelect,
    LogicFieldSelect,
    LogicSelect,
    StructField,
)
from topwrap.model.interface import Interface, InterfaceDefinition, InterfaceMode
from topwrap.model.misc import (
    ElaboratableValue,
    ExtensionData,
    FileReference,
    Identifier,
    Parameter,
)
from topwrap.model.module import Module
from topwrap.resource_field import (
    FileReferenceHandler,
    GitReferenceHandler,
    RepoReferenceHandler,
    ResourceReferenceHandler,
    UriReferenceHandler,
    YamlCommonSchemes,
)


def get_intf_def_by_id_or_error(id: Identifier) -> InterfaceDefinition:
    rsc = util.get_interface_by_id(id)
    if rsc is None:
        raise ValueError(f"No such interface: {id}")
    return rsc.definition


class TestIpCoreDescriptionBackend:
    @pytest.mark.parametrize("top", [simp_top, intf_top, intr_top, hier_top, adv_top])
    def test_ir_examples(self, top: Module):
        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)

        # intr_top and adv_top output YAMLs cannot be parsed using the frontend:
        # intr_top uses a custom Wishbone definition, not the one coming from the repo
        # adv_top uses a custom fake interface with no definition in the repo
        if top not in [intr_top, adv_top]:
            frontend = IPCoreDescriptionFrontend()
            mod = frontend.parse_str(out.content)

            golden = copy.deepcopy(top)
            golden.design = None

            _compare_modules(golden, mod)

    def test_extensions(self):
        top = Module(
            id=Identifier("top"),
            extensions=[
                ExtensionData(name="key0", data=123),
                ExtensionData(name="key1", data="text"),
                ExtensionData(name="key2", data=[1, 2, 3]),
                ExtensionData(name="key3", data={"subkey1": 123}),
            ],
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)

        frontend = IPCoreDescriptionFrontend()
        mod = frontend.parse_str(out.content)

        _compare_modules(top, mod)

    def test_independent_signals(self):
        wishbone = get_intf_def_by_id_or_error(Identifier("wishbone"))

        extp = [
            Port(name="i_wb_stall", direction=PortDirection.IN),
            Port(name="i_wb_err", direction=PortDirection.IN),
        ]
        exti = [
            Interface(
                name="ext_manager",
                mode=InterfaceMode.MANAGER,
                definition=wishbone,
                signals={
                    wishbone.signals.find_by_name_or_error("stall")._id: ReferencedPort.external(
                        extp[0]
                    ),
                    wishbone.signals.find_by_name_or_error("err")._id: ReferencedPort.external(
                        extp[1]
                    ),
                    wishbone.signals.find_by_name_or_error("cyc")._id: None,
                    wishbone.signals.find_by_name_or_error("ack")._id: None,
                },
            )
        ]
        top = Module(
            id=Identifier(name="top"),
            ports=extp,
            interfaces=exti,
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)

        frontend = IPCoreDescriptionFrontend()
        mod = frontend.parse_str(out.content)

        _compare_modules(top, mod)

        intf = mod.interfaces.find_by_name_or_error("ext_manager")
        for sig in ("stall", "err"):
            assert wishbone.signals.find_by_name_or_error(sig) in intf.sliced_signals
        for sig in ("cyc", "ack"):
            assert wishbone.signals.find_by_name_or_error(sig) in intf.independent_signals

    def test_sv_intf(self):
        frontend = SystemVerilogFrontend()

        intf = """
        interface my_intf();
            logic foo;
            logic bar;

            modport manager(input foo, output bar);
            modport subordinate(output foo, input bar);
        endinterface
        """

        src1 = """
        module foo(my_intf.manager mgr);
        endmodule
        """

        src2 = """
        module bar(my_intf.subordinate sub);
        endmodule
        """

        [module1] = frontend.parse_str([intf, src1]).modules
        [module2] = frontend.parse_str([intf, src2]).modules

        backend = IpCoreDescriptionBackend()

        out1 = backend.represent(module1)
        [out1] = backend.serialize(out1)
        tree1 = yaml.safe_load(out1.content)

        out2 = backend.represent(module2)
        [out2] = backend.serialize(out2)
        tree2 = yaml.safe_load(out2.content)

        assert tree1 == {
            "interfaces": {
                "mgr": {
                    "mode": "manager",
                    "signals": {"in": {"foo": None}, "out": {"bar": None}},
                    "type": {
                        "name": "my_intf",
                        "vendor": "vendor",
                        "library": "libdefault",
                        "version": "0.1",
                    },
                }
            },
            "id": {"name": "foo", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
        }

        assert tree2 == {
            "interfaces": {
                "sub": {
                    "mode": "subordinate",
                    "signals": {"out": {"foo": None}, "in": {"bar": None}},
                    "type": {
                        "name": "my_intf",
                        "vendor": "vendor",
                        "library": "libdefault",
                        "version": "0.1",
                    },
                }
            },
            "id": {"name": "bar", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
        }

    def test_complex_port(self):
        ty = Bits(dimensions=[Dimensions(upper=ElaboratableValue(7))])

        ports = [
            Port(
                name="foo", direction=PortDirection.IN, type=ty, default_value=ElaboratableValue(4)
            ),
        ]
        top = Module(
            id=Identifier(name="top"),
            ports=ports,
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {"name": "top", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
            "signals": {
                "in": [
                    {
                        "name": "foo",
                        "bound": ["7", "0"],
                        "default": "4",
                    },
                ],
            },
        }

    def test_multidimensional_port(self):
        ty = Bits(
            dimensions=[
                Dimensions(upper=ElaboratableValue(1), lower=ElaboratableValue(0)),
                Dimensions(upper=ElaboratableValue(7), lower=ElaboratableValue(0)),
            ]
        )

        top = Module(
            id=Identifier(name="top"),
            ports=[
                Port(
                    name="foo",
                    direction=PortDirection.IN,
                    type=ty,
                    default_value=ElaboratableValue(4),
                ),
            ],
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {"name": "top", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
            "signals": {
                "in": [
                    {
                        "name": "foo",
                        "bound": [["1", "0"], ["7", "0"]],
                        "default": "4",
                    },
                ],
            },
        }

        frontend = IPCoreDescriptionFrontend()
        mod = frontend.parse_str(out.content)
        _compare_modules(top, mod)

    def test_parameters(self):
        mod = Module(
            id=Identifier(name="top"),
            parameters=[
                Parameter(name="foo", default_value=ElaboratableValue("32")),
                Parameter(name="bar"),
            ],
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(mod)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {"name": "top", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
            "parameters": {
                "foo": "32",
                "bar": None,
            },
        }

    def test_clocks(self):
        port1 = Port(name="clk_in_1", direction=PortDirection.IN)
        port2 = Port(name="clk_2", direction=PortDirection.IN)
        mod = Module(
            id=Identifier(name="clock_test"),
            clocks=[Clock(name="clk_1", clock=port1), Clock(name="second_clk", clock=port2)],
        )

        backend = IpCoreDescriptionBackend()
        out = backend.represent(mod)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {
                "name": "clock_test",
                "library": "libdefault",
                "vendor": "vendor",
                "version": "0.1",
            },
            "clocks": {"clk_1": {"signal": "clk_in_1"}, "second_clk": {"signal": "clk_2"}},
        }

    def test_resets(self):
        port1 = Port(name="clk_in_1", direction=PortDirection.IN)
        port2 = Port(name="clk_2", direction=PortDirection.IN)
        port3 = Port(name="my_rst_in", direction=PortDirection.IN)
        port4 = Port(name="act_high", direction=PortDirection.IN)
        mod = Module(
            id=Identifier(name="clock_test"),
            clocks=[Clock(name="clk_1", clock=port1), Clock(name="second_clk", clock=port2)],
        )

        rst1 = Reset(name="low_rst", reset=port3, polarity=ResetPolarity.ACTIVE_LOW)
        rst2 = Reset(
            name="high_rst",
            reset=port4,
            polarity=ResetPolarity.ACTIVE_HIGH,
            synchronous_to=mod.clocks[0],
        )
        mod.add_reset(rst1)
        mod.add_reset(rst2)

        backend = IpCoreDescriptionBackend()
        out = backend.represent(mod)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {
                "name": "clock_test",
                "library": "libdefault",
                "vendor": "vendor",
                "version": "0.1",
            },
            "clocks": {"clk_1": {"signal": "clk_in_1"}, "second_clk": {"signal": "clk_2"}},
            "resets": {
                "low_rst": {
                    "signal": "my_rst_in",
                    "polarity": "active low",
                },
                "high_rst": {
                    "signal": "act_high",
                    "polarity": "active high",
                    "synchronous_to": "clk_1",
                },
            },
        }

    def test_struct_port(self):
        ty = BitStruct(
            name="some_type",
            fields=[
                StructField(
                    name="some_field",
                    type=Bit(),
                ),
            ],
        )

        ports = [
            Port(name="foo", direction=PortDirection.IN, type=ty),
        ]
        top = Module(
            id=Identifier(name="top"),
            ports=ports,
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {"name": "top", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
            "signals": {
                "in": [
                    {
                        "name": "foo",
                        "type": "some_type",
                    },
                ],
            },
            "types": {
                "some_type": {
                    "members": [
                        {
                            "name": "some_field",
                            "type": [0, 0],
                        },
                    ],
                },
            },
        }

    def test_intf_signal_path(self):
        wishbone = get_intf_def_by_id_or_error(Identifier("wishbone"))

        field_ty = Bits(dimensions=[Dimensions(upper=ElaboratableValue(7))])
        ty = BitStruct(
            name="some_type",
            fields=[
                StructField(
                    name="some_field",
                    type=field_ty,
                ),
            ],
        )

        ports = [
            Port(name="foo", direction=PortDirection.IN, type=ty),
        ]
        intfs = [
            Interface(
                name="ext_manager",
                mode=InterfaceMode.MANAGER,
                definition=wishbone,
                signals={
                    wishbone.signals.find_by_name_or_error("stall")._id: ReferencedPort.external(
                        ports[0],
                        select=LogicSelect(
                            logic=Bit(),
                            ops=[
                                LogicFieldSelect(
                                    field=ty.fields[0],
                                ),
                                LogicBitSelect(
                                    slice=Dimensions(),
                                ),
                            ],
                        ),
                    ),
                },
            ),
        ]
        top = Module(
            id=Identifier(name="top"),
            ports=ports,
            interfaces=intfs,
        )

        backend = IpCoreDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        assert tree == {
            "id": {"name": "top", "library": "libdefault", "vendor": "vendor", "version": "0.1"},
            "signals": {
                "in": [
                    {
                        "name": "foo",
                        "type": "some_type",
                    },
                ],
            },
            "types": {
                "some_type": {
                    "members": [
                        {
                            "name": "some_field",
                            "type": ["7", "0"],
                        },
                    ],
                },
            },
            "interfaces": {
                "ext_manager": {
                    "type": {
                        "vendor": "vendor",
                        "library": "libdefault",
                        "name": "wishbone",
                        "version": "0.1",
                    },
                    "mode": "manager",
                    "signals": {
                        "in": {
                            "stall": {
                                "path": "foo.some_field[0]",
                            },
                        },
                    },
                },
            },
        }


class TestDesignDescriptionBackend:
    @pytest.mark.parametrize(
        "src",
        [
            Path("examples/constant/project.yaml"),
            Path("examples/hierarchy/project.yaml"),
            Path("examples/hdmi/project.yaml"),
            Path("examples/pwm/project.yaml"),
            Path("examples/ir_examples/inverted/design.yaml"),
            Path("examples/ir_examples/clocks/design.yaml"),
            Path("examples/ir_examples/interconnect/design.yaml"),
            Path("examples/ir_examples/interface/design.yaml"),
            Path("examples/ir_examples/simple/design.yaml"),
        ],
    )
    def test_examples(self, src: Path):
        front = DesignDescriptionFrontend()
        back = DesignDescriptionBackend()

        orig_des, _ = front.parse_file(src)

        out = back.represent(orig_des.parent)
        [out] = back.serialize(out)

        new_des, _ = front.parse_str(out.content)

        _compare_modules(orig_des.parent, new_des.parent)

    def test_extensions(self):
        design = Design(
            extensions=[
                ExtensionData(name="key0", data=123),
                ExtensionData(name="key1", data="text"),
                ExtensionData(name="key2", data=[1, 2, 3]),
                ExtensionData(name="key3", data={"subkey1": 123}),
            ]
        )

        top = Module(id=Identifier("top"), design=design)

        backend = DesignDescriptionBackend()

        out = backend.represent(top)
        [out] = backend.serialize(out)

        frontend = DesignDescriptionFrontend()
        design_parsed, _ = frontend.parse_str(out.content)

        _compare_designs(design, design_parsed)

    def test_intr_comp_intfs(self):
        wishbone = get_intf_def_by_id_or_error(Identifier("wishbone"))

        topp = [
            Port(name="clk", direction=PortDirection.IN),
            Port(name="rst", direction=PortDirection.IN),
        ]
        subi = [
            Interface(
                name="ext_mgr",
                mode=InterfaceMode.MANAGER,
                definition=wishbone,
                signals={},
            ),
            Interface(
                name="ext_sub",
                mode=InterfaceMode.SUBORDINATE,
                definition=wishbone,
                signals={},
            ),
        ]
        sub = Module(
            id=Identifier(name="sub"),
            ports=[],
            interfaces=subi,
            refs=[FileReference(Path("/this/does/not/exist"))],
        )
        comp = ModuleInstance(name="sub", module=sub)

        des = Design(
            components=[comp],
            interconnects=[
                WishboneInterconnect(
                    name="",
                    clock=ReferencedPort.external(topp[0]),
                    reset=ReferencedPort.external(topp[1]),
                    params=WishboneRRParams(
                        data_width=ElaboratableValue(32),
                        addr_width=ElaboratableValue(32),
                        granularity=8,
                        features=set(),
                    ),
                    managers={
                        ReferencedInterface(
                            io=subi[0], instance=comp
                        )._id: WishboneRRManagerParams(),
                    },
                    subordinates={
                        ReferencedInterface(
                            io=subi[1], instance=comp
                        )._id: WishboneRRSubordinateParams(),
                    },
                )
            ],
        )
        top = Module(
            id=Identifier(name="top"),
            ports=topp,
            design=des,
        )

        back = DesignDescriptionBackend()

        out = back.represent(top)
        [out] = back.serialize(out)

    def test_config_output(self):
        # Combinations of configuration options
        missing = [True, False]
        force_interface_compliance: list[Optional[bool]] = [None, False, True]
        repositories: list[dict[str, ResourceReferenceHandler]] = [
            {},
            {"a": RepoReferenceHandler("abc", ["def"])},
            {"a": UriReferenceHandler("abc", ["def"])},
            {"a": GitReferenceHandler("abc", ["def"])},
            {"a": FileReferenceHandler("abc", ["def"])},
        ]

        # Check for full coverage
        required_handlers = YamlCommonSchemes.handlers
        assert all(
            any(isinstance(h, req_h) for r in repositories for h in r.values())
            for req_h in required_handlers
        ), "test_config_output does not cover all reference handlers"

        for is_missing, fic, rep in product(missing, force_interface_compliance, repositories):
            cnf = ConfigDescription(fic, rep)

            des = Design(config=cnf if not is_missing else None)
            mod = Module(
                id=Identifier("top"),
                design=des,
            )

            back = DesignDescriptionBackend()
            out = back.represent(mod)

            out_cnf = out.description.config

            if is_missing:
                assert out_cnf is None

                [out] = back.serialize(out)

                design_yaml = yaml.safe_load(out.content)
                assert isinstance(design_yaml, dict)
                assert "config" not in design_yaml
            else:
                assert out_cnf is not None
                assert out_cnf.force_interface_compliance == fic
                assert out_cnf.repositories == rep

                [out] = back.serialize(out)

                design_yaml = yaml.safe_load(out.content)
                assert isinstance(design_yaml, dict)

                if fic is None and not rep:
                    assert "config" not in design_yaml
                else:
                    assert "config" in design_yaml
                    config_dict = design_yaml["config"]
                    assert isinstance(config_dict, dict)

                    if fic is None:
                        assert "force_interface_compliance" not in config_dict
                    else:
                        assert "force_interface_compliance" in config_dict
                        assert config_dict["force_interface_compliance"] == fic

                    if not rep:
                        assert "repositories" not in config_dict
                    else:
                        assert "repositories" in config_dict
                        repo_dict = config_dict["repositories"]
                        assert isinstance(repo_dict, dict)

                        expected_obj: dict[str, str] = {name: h.to_str() for name, h in rep.items()}
                        assert repo_dict == expected_obj

    def test_multidimensional_top_level_ports_roundtrip(self):
        design_yaml = """
            name: top
            external:
              ports:
                in:
                  - name: in_arr
                    bound: [[1, 0], [7, 0], [3, 0]]
                out:
                  - name: out_vec
                    bound: [[15, 0]]
            """

        front = DesignDescriptionFrontend()
        orig_des, _ = front.parse_str(design_yaml)

        back = DesignDescriptionBackend()
        out = back.represent(orig_des.parent)
        [out] = back.serialize(out)

        new_des, _ = front.parse_str(out.content)

        in_arr = new_des.parent.ports.find_by_name_or_error("in_arr")
        out_vec = new_des.parent.ports.find_by_name_or_error("out_vec")

        assert isinstance(in_arr.type, LogicArray)
        assert in_arr.type.dimensions == [
            Dimensions(upper=ElaboratableValue(1), lower=ElaboratableValue(0)),
            Dimensions(upper=ElaboratableValue(7), lower=ElaboratableValue(0)),
            Dimensions(upper=ElaboratableValue(3), lower=ElaboratableValue(0)),
        ]
        assert isinstance(out_vec.type, LogicArray)
        assert out_vec.type.dimensions == [
            Dimensions(upper=ElaboratableValue(15), lower=ElaboratableValue(0))
        ]


class TestDesignPositionsBackend:
    def test_positions(self):
        pos = {
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

        backend = DesignPositionsBackend()
        out = backend.represent("name", pos)
        [out] = backend.serialize(out)

        assert out.filename == "name.kpm_positions.yaml"

        tree = yaml.safe_load(out.content)
        assert tree == {
            "modules": [
                {
                    "id": {
                        "library": "libdefault",
                        "vendor": "vendor",
                        "version": "0.1",
                        "name": "foo",
                    },
                    "components": [
                        {"name": "comp1", "position": [123.0, 456.0]},
                        {"name": "comp2", "position": [21.0, 54.0]},
                    ],
                    "inverters": [
                        {
                            "source": "inp",
                            "target": ["comp1", "outp"],
                            "position": [22.0, 33.0],
                        },
                    ],
                },
                {
                    "id": {
                        "library": "libdefault",
                        "vendor": "vendor",
                        "version": "0.1",
                        "name": "bar",
                    },
                    "externals": [
                        {"name": "a", "position": [1.0, 2.0]},
                    ],
                    "constants": [
                        {"name": "0", "position": [5.0, 4.0]},
                    ],
                    "clock_domains": [
                        {"name": "default", "position": [9.0, 3.0]},
                    ],
                    "reset_domains": [
                        {"name": "default", "position": [9.0, 5.0]},
                    ],
                    "interconnects": [
                        {"name": "intercon1", "position": [10.0, 7.0]},
                    ],
                    "identifier": [-1.0, -1.0],
                },
            ],
        }
