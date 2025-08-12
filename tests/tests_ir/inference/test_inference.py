# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import pytest

from tests.data.data_ir.inference.ahb_if import ahblite_intf
from tests.data.data_ir.inference.axi_if import axi4_intf
from tests.data.data_ir.inference.axilite_if import axi4lite_intf
from tests.data.data_ir.inference.bbox_if import bbox_full_intf, bbox_in_only_intf, bbox_intf
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
            bbox, all_intf_defs, grouping_hints={"bbox": ["bbox_in", "bbox_out"]}
        )
        map_interfaces_to_module([mapping], all_intf_defs, bbox)

        assert len(bbox.interfaces) == 1

        bbox = bbox.interfaces.find_by_name_or_error("bbox")

        assert bbox.definition == bbox_full_intf
        assert bbox.mode == InterfaceMode.MANAGER

        bbox_used_ports = {x.io.name if x else "?" for _, x in bbox.signals.items()}
        assert bbox_used_ports == {"bbox_in", "bbox_out"}
