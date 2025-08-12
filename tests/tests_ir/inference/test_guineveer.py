# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import copy

from tests.data.data_ir.inference.guineveer_axi_to_ahb import axi_to_ahb
from tests.data.data_ir.inference.guineveer_i3c import i3c
from tests.data.data_ir.inference.guineveer_intercon import axi_intercon
from tests.data.data_ir.inference.guineveer_sram import sram
from tests.data.data_ir.inference.guineveer_uart import uart
from tests.data.data_ir.inference.guineveer_veer_el2 import veer_el2
from tests.data.data_ir.inference.pulp_axi_cdc import axi_cdc
from tests.data.data_ir.inference.pulp_axi_demux import axi_demux
from tests.tests_ir.inference.test_inference import _all_interfaces, all_intf_defs
from topwrap.model.inference.inference import infer_interfaces_from_module
from topwrap.model.inference.mapping import map_interfaces_to_module


class TestGuineveerInterfaceInference:
    """
    Tests for the infer_interfaces_from_module function. Tests performing inference on various
    modules with port lists derived from modules used in Guineveer.
    """

    def test_axi_intercon(self):
        mod = copy.deepcopy(axi_intercon)

        assert len(mod.interfaces) == 0

        mapping = infer_interfaces_from_module(mod, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {
            "uart": "AXI4",
            "mem": "AXI4",
            "i3c": "AXI4",
        }
        assert s_intfs == {
            "veer_lsu": "AXI4",
            "veer_ifu": "AXI4",
        }

    def test_axi_to_ahb(self):
        mod = copy.deepcopy(axi_to_ahb)

        assert len(axi_to_ahb.interfaces) == 0

        mapping = infer_interfaces_from_module(mod, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {
            "ahb": "AHBLite",
        }
        assert s_intfs == {
            "axi": "AXI4Lite",
        }

    def test_uart(self):
        mod = copy.deepcopy(uart)

        assert len(uart.interfaces) == 0

        mapping = infer_interfaces_from_module(mod, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {}
        assert s_intfs == {
            "AHBLite": "AHBLite",
        }

    def test_i3c(self):
        mod = copy.deepcopy(i3c)

        assert len(mod.interfaces) == 0

        mapping = infer_interfaces_from_module(mod, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {}
        assert s_intfs == {
            "AXI4": "AXI4",
        }

    def test_veer_el2(self):
        mod = copy.deepcopy(veer_el2)

        assert len(mod.interfaces) == 0

        mapping = infer_interfaces_from_module(mod, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {
            "ifu_axi": "AXI4",
            "lsu_axi": "AXI4",
            "sb_axi": "AXI4",
        }
        assert s_intfs == {
            "dma_axi": "AXI4",
        }

    def test_axi_cdc(self):
        mod = copy.deepcopy(axi_cdc)

        assert len(mod.interfaces) == 0

        mapping = infer_interfaces_from_module(
            mod,
            all_intf_defs,
            grouping_hints={
                "src": ["src_req_i", "src_resp_o"],
                "dst": ["dst_req_o", "dst_resp_i"],
            },
        )
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {
            "dst": "AXI4",
        }
        assert s_intfs == {
            "src": "AXI4",
        }

    def test_sram(self):
        mod = copy.deepcopy(sram)

        assert len(mod.interfaces) == 0

        mapping = infer_interfaces_from_module(
            mod,
            all_intf_defs,
            grouping_hints={
                "axi": ["axi_req_i", "axi_resp_o"],
            },
        )
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {}
        assert s_intfs == {
            "axi": "AXI4",
        }

    def test_axi_demux(self):
        mod = copy.deepcopy(axi_demux)

        assert len(mod.interfaces) == 0

        mapping = infer_interfaces_from_module(
            mod,
            all_intf_defs,
            grouping_hints={
                "slv": ["slv_req_i", "slv_resp_o"],
                "mst": ["mst_reqs_o", "mst_resps_i"],
            },
        )
        map_interfaces_to_module([mapping], all_intf_defs, mod)

        m_intfs, s_intfs = _all_interfaces(mod)

        assert m_intfs == {
            "mst[0]": "AXI4",
            "mst[1]": "AXI4",
            "mst[2]": "AXI4",
            "mst[3]": "AXI4",
        }
        assert s_intfs == {
            "slv": "AXI4",
        }
