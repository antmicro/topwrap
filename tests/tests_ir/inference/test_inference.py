# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


from pathlib import Path

import pytest
import yaml

from tests.data.data_ir.inference.ahb_if import ahblite_intf
from tests.data.data_ir.inference.axi_if import axi4_intf
from tests.data.data_ir.inference.axilite_if import axi4lite_intf
from tests.data.data_ir.inference.bbox_if import bbox_full_intf, bbox_in_only_intf, bbox_intf
from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.backend.yaml.common.interface_schema import InterfaceDefinitionDescription
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.yaml.interface import InterfaceDefinitionDescriptionFrontend
from topwrap.model.connections import Port, PortDirection, ReferencedPort
from topwrap.model.design import Design
from topwrap.model.hdl_types import Bit, BitStruct, StructField
from topwrap.model.inference.inference import infer_interfaces_from_module
from topwrap.model.inference.mapping import InterfaceMappingError, map_interfaces_to_module
from topwrap.model.interface import (
    Interface,
    InterfaceMode,
)
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

all_intf_defs = [
    axi4lite_intf,
    axi4_intf,
    bbox_intf,
    bbox_full_intf,
    bbox_in_only_intf,
    ahblite_intf,
]


def _all_interfaces(module: Module) -> tuple[dict[str, str], dict[str, str]]:
    manager_intfs = {
        intf.name: intf.definition.id.name
        for intf in module.interfaces
        if intf.mode == InterfaceMode.MANAGER
    }
    subordinate_intfs = {
        intf.name: intf.definition.id.name
        for intf in module.interfaces
        if intf.mode == InterfaceMode.SUBORDINATE
    }
    return (manager_intfs, subordinate_intfs)


class TestInterfaceInference:
    """
    Tests for the infer_interfaces_from_module function. Tests performing inference on various
    simple modules with a made-up interfaces.
    """

    def test_basic(self):
        bbox_exts = [
            Port(name="i_bbox1_foo", direction=PortDirection.IN),
            Port(name="o_bbox1_bar", direction=PortDirection.OUT),
            Port(name="i_bbox2_foo", direction=PortDirection.IN),
            Port(name="o_bbox2_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        m_intfs, s_intfs = _all_interfaces(bbox)

        assert m_intfs == {
            "bbox1": "Blackbox",
            "bbox2": "Blackbox",
        }
        assert s_intfs == {}

    def test_basic_camel_case(self):
        bbox_exts = [
            Port(name="i_bboxCamelCase1Foo", direction=PortDirection.IN),
            Port(name="o_bboxCamelCase1Bar", direction=PortDirection.OUT),
            Port(name="i_bboxCamelCase2Foo", direction=PortDirection.IN),
            Port(name="o_bboxCamelCase2Bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        m_intfs, s_intfs = _all_interfaces(bbox)

        assert m_intfs == {
            "bboxCamelCase1": "Blackbox",
            "bboxCamelCase2": "Blackbox",
        }
        assert s_intfs == {}

    def test_port_name_collision(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="foo_i", direction=PortDirection.IN),
            Port(name="foo_i_1", direction=PortDirection.IN),
            Port(name="bar_o", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        m_intfs, s_intfs = _all_interfaces(bbox)

        assert m_intfs == {
            "Blackbox": "Blackbox",
        }
        assert s_intfs == {}

        foo_ref = bbox.interfaces[0].signals[bbox_intf.signals[0]._id]
        assert foo_ref
        assert foo_ref.io.name == "i_foo"

        bar_ref = bbox.interfaces[0].signals[bbox_intf.signals[1]._id]
        assert bar_ref
        assert bar_ref.io.name == "bar_o"

    def test_intf_name_collision(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
            Port(name="i_bbox2_foo", direction=PortDirection.IN),
            Port(name="o_bbox2_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            interfaces=[
                Interface(
                    definition=bbox_intf,
                    mode=InterfaceMode.MANAGER,
                    name="Blackbox",
                    signals={
                        bbox_intf.signals[0]._id: ReferencedPort.external(bbox_exts[2]),
                        bbox_intf.signals[1]._id: ReferencedPort.external(bbox_exts[3]),
                    },
                ),
            ],
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        m_intfs, s_intfs = _all_interfaces(bbox)

        assert m_intfs == {
            "Blackbox": "Blackbox",
            "Blackbox_1": "Blackbox",
        }
        assert s_intfs == {}

    def test_no_mode_match(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.INOUT),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 0

    def test_mode_no_consensus(self):
        bbox_exts = [
            Port(name="foo", direction=PortDirection.IN),
            Port(name="bar", direction=PortDirection.IN),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 0

    def test_mode_mismatch_directions(self):
        # Deduced manager.
        bbox_exts = [
            Port(name="foo", direction=PortDirection.IN),
            Port(name="bar", direction=PortDirection.IN),
            Port(name="baz", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        with pytest.raises(InterfaceMappingError, match="has wrong direction"):
            map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 0

        # Deduced subordinate.
        bbox_exts = [
            Port(name="foo", direction=PortDirection.OUT),
            Port(name="bar", direction=PortDirection.OUT),
            Port(name="baz", direction=PortDirection.IN),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        with pytest.raises(InterfaceMappingError, match="has wrong direction"):
            map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 0

    def test_struct_inference(self):
        inbox_struct = BitStruct(
            name="inbox_struct",
            fields=[
                StructField(name="in1", type=Bit()),
                StructField(name="IN2", type=Bit()),
            ],
        )

        bbox_exts = [
            Port(name="inbox1", direction=PortDirection.IN, type=inbox_struct),
            Port(name="inbox2", direction=PortDirection.OUT, type=inbox_struct),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(bbox, all_intf_defs)
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 2

        inbox1 = bbox.interfaces.find_by_name_or_error("inbox1")
        inbox2 = bbox.interfaces.find_by_name_or_error("inbox2")

        assert inbox1.definition == bbox_in_only_intf
        assert inbox1.mode == InterfaceMode.MANAGER

        assert inbox2.definition == bbox_in_only_intf
        assert inbox2.mode == InterfaceMode.SUBORDINATE

        inbox1_used_ports = {x.io.name if x else "?" for _, x in inbox1.signals.items()}
        assert inbox1_used_ports == {"inbox1"}

        inbox2_used_ports = {x.io.name if x else "?" for _, x in inbox2.signals.items()}
        assert inbox2_used_ports == {"inbox2"}

    def test_hint_struct_inference(self):
        bbox_in = BitStruct(
            name="bbox_in",
            fields=[
                StructField(name="foo", type=Bit()),
            ],
        )

        bbox_out = BitStruct(
            name="bbox_out",
            fields=[
                StructField(name="bar", type=Bit()),
                StructField(name="baz", type=Bit()),
            ],
        )

        bbox_exts = [
            Port(name="bbox_in", direction=PortDirection.IN, type=bbox_in),
            Port(name="bbox_out", direction=PortDirection.OUT, type=bbox_out),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = infer_interfaces_from_module(
            bbox,
            all_intf_defs,
            grouping_hints={
                "bbox_in": "bbox",
                "bbox_out": "bbox",
            },
        )
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 1

        bbox = bbox.interfaces.find_by_name_or_error("bbox")

        assert bbox.definition == bbox_full_intf
        assert bbox.mode == InterfaceMode.MANAGER

        bbox_used_ports = {x.io.name if x else "?" for _, x in bbox.signals.items()}
        assert bbox_used_ports == {"bbox_in", "bbox_out"}

    def test_sv_struct_port_inference(self):
        sv = SystemVerilogFrontend()
        sv_mod = sv.parse_files(
            [Path("tests/data/data_ir/inference/structs/sram_wrapper.sv")]
        ).modules[0]

        with open(
            "tests/data/data_ir/inference/structs/vendor_libdefault_AXIstructs.yaml", "r"
        ) as f:
            intf_def = InterfaceDefinitionDescription.from_yaml(f.read())
            intf = InterfaceDefinitionDescriptionFrontend().parse(intf_def)

        mapping = infer_interfaces_from_module(
            sv_mod,
            [intf],
            grouping_hints={
                "axi_req": "axi",
                "axi_resp": "axi",
            },
        )
        map_interfaces_to_module([mapping], [intf], sv_mod)

        backend = IpCoreDescriptionBackend()

        out = backend.represent(sv_mod)
        [out] = backend.serialize(out)
        tree = yaml.safe_load(out.content)

        # Parsing SV does not yield ports in a fixed order due to dict randomness
        tree["signals"]["in"].sort(key=lambda x: x["name"])

        assert tree == {
            "id": {"library": "libdefault", "name": "sram_wrapper", "vendor": "vendor"},
            "interfaces": {
                "axi": {
                    "mode": "subordinate",
                    "signals": {
                        "in": {
                            "ARADDR": {"path": "axi_req.ar.addr"},
                            "ARBURST": {"path": "axi_req.ar.burst"},
                            "ARCACHE": {"path": "axi_req.ar.cache"},
                            "ARLEN": {"path": "axi_req.ar.len"},
                            "ARLOCK": {"path": "axi_req.ar.lock"},
                            "ARPROT": {"path": "axi_req.ar.prot"},
                            "ARQOS": {"path": "axi_req.ar.qos"},
                            "ARREGION": {"path": "axi_req.ar.region"},
                            "ARSIZE": {"path": "axi_req.ar.size"},
                            "ARUSER": {"path": "axi_req.ar.user"},
                            "ARVALID": {"path": "axi_req.ar_valid"},
                            "AWADDR": {"path": "axi_req.aw.addr"},
                            "AWATOP": {"path": "axi_req.aw.atop"},
                            "AWBURST": {"path": "axi_req.aw.burst"},
                            "AWCACHE": {"path": "axi_req.aw.cache"},
                            "AWID": {"path": "axi_req.aw.id"},
                            "AWLEN": {"path": "axi_req.aw.len"},
                            "AWLOCK": {"path": "axi_req.aw.lock"},
                            "AWPROT": {"path": "axi_req.aw.prot"},
                            "AWQOS": {"path": "axi_req.aw.qos"},
                            "AWREGION": {"path": "axi_req.aw.region"},
                            "AWSIZE": {"path": "axi_req.aw.size"},
                            "AWUSER": {"path": "axi_req.aw.user"},
                            "AWVALID": {"path": "axi_req.aw_valid"},
                            "BREADY": {"path": "axi_req.b_ready"},
                            "RREADY": {"path": "axi_req.r_ready"},
                            "WDATA": {"path": "axi_req.w.data"},
                            "WLAST": {"path": "axi_req.w.last"},
                            "WSTRB": {"path": "axi_req.w.strb"},
                            "WUSER": {"path": "axi_req.w.user"},
                            "WVALID": {"path": "axi_req.w_valid"},
                        },
                        "out": {
                            "ARREADY": {"path": "axi_resp.ar_ready"},
                            "AWREADY": {"path": "axi_resp.aw_ready"},
                            "BID": {"path": "axi_resp.b.id"},
                            "BRESP": {"path": "axi_resp.b.resp"},
                            "BUSER": {"path": "axi_resp.b.user"},
                            "BVALID": {"path": "axi_resp.b_valid"},
                            "RDATA": {"path": "axi_resp.r.data"},
                            "RID": {"path": "axi_resp.r.id"},
                            "RLAST": {"path": "axi_resp.r.last"},
                            "RRESP": {"path": "axi_resp.r.resp"},
                            "RUSER": {"path": "axi_resp.r.user"},
                            "RVALID": {"path": "axi_resp.r_valid"},
                            "WREADY": {"path": "axi_resp.w_ready"},
                        },
                    },
                    "type": {
                        "vendor": "vendor",
                        "library": "libdefault",
                        "name": "AXIstructs",
                    },
                }
            },
            "signals": {
                "in": [
                    {"name": "axi_req", "type": "axi_req_t"},
                    {"name": "clk_i"},
                    {"name": "rst_ni"},
                ],
                "out": [{"name": "axi_resp", "type": "axi_resp_t"}],
            },
            "types": {
                "axi_req_t": {
                    "members": [
                        {
                            "name": "aw",
                            "type": {
                                "members": [
                                    {"name": "id", "type": ["5", "0"]},
                                    {"name": "addr", "type": ["31", "0"]},
                                    {"name": "len", "type": ["7", "0"]},
                                    {"name": "size", "type": ["2", "0"]},
                                    {"name": "burst", "type": ["1", "0"]},
                                    {"name": "lock", "type": [0, 0]},
                                    {"name": "cache", "type": ["3", "0"]},
                                    {"name": "prot", "type": ["2", "0"]},
                                    {"name": "qos", "type": ["3", "0"]},
                                    {"name": "region", "type": ["3", "0"]},
                                    {"name": "atop", "type": ["5", "0"]},
                                    {"name": "user", "type": [0, 0]},
                                ]
                            },
                        },
                        {"name": "aw_valid", "type": [0, 0]},
                        {
                            "name": "w",
                            "type": {
                                "members": [
                                    {"name": "data", "type": ["63", "0"]},
                                    {"name": "strb", "type": ["7", "0"]},
                                    {"name": "last", "type": [0, 0]},
                                    {"name": "user", "type": [0, 0]},
                                ]
                            },
                        },
                        {"name": "w_valid", "type": [0, 0]},
                        {"name": "b_ready", "type": [0, 0]},
                        {
                            "name": "ar",
                            "type": {
                                "members": [
                                    {"name": "id", "type": ["5", "0"]},
                                    {"name": "addr", "type": ["31", "0"]},
                                    {"name": "len", "type": ["7", "0"]},
                                    {"name": "size", "type": ["2", "0"]},
                                    {"name": "burst", "type": ["1", "0"]},
                                    {"name": "lock", "type": [0, 0]},
                                    {"name": "cache", "type": ["3", "0"]},
                                    {"name": "prot", "type": ["2", "0"]},
                                    {"name": "qos", "type": ["3", "0"]},
                                    {"name": "region", "type": ["3", "0"]},
                                    {"name": "user", "type": [0, 0]},
                                ]
                            },
                        },
                        {"name": "ar_valid", "type": [0, 0]},
                        {"name": "r_ready", "type": [0, 0]},
                    ]
                },
                "axi_resp_t": {
                    "members": [
                        {"name": "aw_ready", "type": [0, 0]},
                        {"name": "ar_ready", "type": [0, 0]},
                        {"name": "w_ready", "type": [0, 0]},
                        {"name": "b_valid", "type": [0, 0]},
                        {
                            "name": "b",
                            "type": {
                                "members": [
                                    {"name": "id", "type": ["5", "0"]},
                                    {"name": "resp", "type": ["1", "0"]},
                                    {"name": "user", "type": [0, 0]},
                                ]
                            },
                        },
                        {"name": "r_valid", "type": [0, 0]},
                        {
                            "name": "r",
                            "type": {
                                "members": [
                                    {"name": "id", "type": ["5", "0"]},
                                    {"name": "data", "type": ["63", "0"]},
                                    {"name": "resp", "type": ["1", "0"]},
                                    {"name": "last", "type": [0, 0]},
                                    {"name": "user", "type": [0, 0]},
                                ]
                            },
                        },
                    ]
                },
            },
        }
