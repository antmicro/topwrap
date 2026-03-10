# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import copy

import pytest
import yaml

from examples.ir_examples.modules import (
    adv_top,
    hier_top,
    intf_top,
    intr_top,
    simp_top,
)
from tests.tests_ir.test_kpm_non_destructive import _compare_modules
from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.yaml.ip_core import InterfaceDescriptionFrontend, IPCoreDescriptionFrontend
from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import Identifier
from topwrap.model.module import Module


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

    def test_independent_signals(self):
        wishbone = InterfaceDescriptionFrontend().from_loaded("wishbone")
        assert wishbone

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
                    "type": "my_intf",
                }
            },
            "name": "foo",
        }

        assert tree2 == {
            "interfaces": {
                "sub": {
                    "mode": "subordinate",
                    "signals": {"out": {"foo": None}, "in": {"bar": None}},
                    "type": "my_intf",
                }
            },
            "name": "bar",
        }
