# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import pytest
from marshmallow import ValidationError

from tests.data.data_ir.inference.bbox_if import bbox_intf
from topwrap.model.connections import Port, PortDirection
from topwrap.model.design import Design
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    ElaboratableValue,
    LogicArray,
    StructField,
)
from topwrap.model.inference.mapping import (
    InterfaceMappingError,
    InterfacePortMapping,
    map_interfaces_to_module,
)
from topwrap.model.interface import (
    InterfaceMode,
)
from topwrap.model.misc import Identifier
from topwrap.model.module import Module


class TestInterfaceMapping:
    """
    Tests for the map_interfaces_to_module function and InterfacePortMapping class. Tests applying
    various valid mappings onto modules, and trying to parse and apply invalid mappings.
    """

    def test_noop_mapping(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: not_bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo
              bar: o_bar
        """)

        map_interfaces_to_module([mapping], [bbox_intf], bbox)

        assert len(bbox.interfaces) == 0

    def test_simple_mapping(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
            Port(name="o_sub_foo", direction=PortDirection.OUT),
            Port(name="i_sub_bar", direction=PortDirection.IN),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox_root:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo
              bar: o_bar
          bbox_sub:
            interface:
              name: Blackbox
            mode: SUBORDINATE
            signals:
              foo: o_sub_foo
              bar: i_sub_bar
        """)

        map_interfaces_to_module([mapping], [bbox_intf], bbox)

        assert len(bbox.interfaces) == 2

        root = bbox.interfaces.find_by_name_or_error("bbox_root")
        sub = bbox.interfaces.find_by_name_or_error("bbox_sub")

        assert root.definition == bbox_intf
        assert sub.definition == bbox_intf

        assert root.mode == InterfaceMode.MANAGER
        assert sub.mode == InterfaceMode.SUBORDINATE

        root_used_ports = {x.io.name if x else "?" for _, x in root.signals.items()}
        assert root_used_ports == {"i_foo", "o_bar"}

        sub_used_ports = {x.io.name if x else "?" for _, x in sub.signals.items()}
        assert sub_used_ports == {"i_sub_bar", "o_sub_foo"}

    def test_struct_mapping(self):
        struct_with_one_bit = BitStruct(
            name="struct_with_one_bit",
            fields=[
                StructField(name="single_bit", type=Bit()),
            ],
        )

        struct_with_two_bits = BitStruct(
            name="struct_with_two_bits",
            fields=[
                StructField(
                    name="two_bits", type=Bits(dimensions=[Dimensions(ElaboratableValue(1))])
                ),
            ],
        )

        nested_struct_with_one_bit = BitStruct(
            name="nested_struct_with_one_bit",
            fields=[
                StructField(name="single_bit_struct", type=struct_with_one_bit),
            ],
        )

        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN, type=struct_with_one_bit),
            Port(name="o_bar", direction=PortDirection.OUT, type=nested_struct_with_one_bit),
            Port(name="o_sub_foo", direction=PortDirection.OUT, type=nested_struct_with_one_bit),
            Port(name="i_sub_bar", direction=PortDirection.IN, type=struct_with_two_bits),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox_root:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo.single_bit
              bar: o_bar.single_bit_struct.single_bit
          bbox_sub:
            interface:
              name: Blackbox
            mode: SUBORDINATE
            signals:
              foo: o_sub_foo.single_bit_struct.single_bit
              bar: i_sub_bar.two_bits[1:2]
        """)

        map_interfaces_to_module([mapping], [bbox_intf], bbox)

        assert len(bbox.interfaces) == 2

        root = bbox.interfaces.find_by_name_or_error("bbox_root")
        sub = bbox.interfaces.find_by_name_or_error("bbox_sub")

        assert root.definition == bbox_intf
        assert sub.definition == bbox_intf

        assert root.mode == InterfaceMode.MANAGER
        assert sub.mode == InterfaceMode.SUBORDINATE

        root_used_ports = {x.io.name if x else "?" for _, x in root.signals.items()}
        assert root_used_ports == {"i_foo", "o_bar"}

        sub_used_ports = {x.io.name if x else "?" for _, x in sub.signals.items()}
        assert sub_used_ports == {"i_sub_bar", "o_sub_foo"}

    def test_array_of_structs(self):
        struct_with_one_bit = BitStruct(
            name="struct_with_one_bit",
            fields=[
                StructField(name="single_bit", type=Bit()),
            ],
        )

        struct_with_array = BitStruct(
            name="struct_with_two_bits",
            fields=[
                StructField(
                    name="two_bits",
                    type=LogicArray(
                        item=struct_with_one_bit, dimensions=[Dimensions(ElaboratableValue(1))]
                    ),
                ),
            ],
        )

        bbox_exts = [
            Port(name="i_foos", direction=PortDirection.IN, type=struct_with_array),
            Port(name="o_bars", direction=PortDirection.OUT, type=struct_with_array),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox1:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foos.two_bits[0].single_bit
              bar: o_bars.two_bits[0].single_bit
          bbox2:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foos.two_bits[1].single_bit
              bar: o_bars.two_bits[1].single_bit
        """)

        map_interfaces_to_module([mapping], [bbox_intf], bbox)

        assert len(bbox.interfaces) == 2

        one = bbox.interfaces.find_by_name_or_error("bbox1")
        two = bbox.interfaces.find_by_name_or_error("bbox2")

        assert one.definition == bbox_intf
        assert two.definition == bbox_intf

        assert one.mode == InterfaceMode.MANAGER
        assert two.mode == InterfaceMode.MANAGER

        one_used_ports = {x.io.name if x else "?" for _, x in one.signals.items()}
        assert one_used_ports == {"i_foos", "o_bars"}

        two_used_ports = {x.io.name if x else "?" for _, x in two.signals.items()}
        assert two_used_ports == {"i_foos", "o_bars"}

    def test_to_from_yaml(self):
        in_mapping = InterfacePortMapping.from_yaml("""
        id:
          name: hello
        interfaces:
          bbox1:
            interface:
              name: world
            mode: MANAGER
            signals:
              foo: mst_reqs_o[2].ar.addr[3:0]
              bar: mst_resps_o[2].r.data[7:4]
            clock: clk_i
            reset: rst_ni
        """)

        out_mapping = InterfacePortMapping.from_yaml(in_mapping.to_yaml())

        assert in_mapping == out_mapping

    def test_wrong_intf(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Badbox
            mode: MANAGER
            signals:
              foo: i_foo
        """)

        with pytest.raises(InterfaceMappingError, match=r"references unknown interface"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_missing_required(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo
        """)

        with pytest.raises(InterfaceMappingError, match=r"is not assigned to anything"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_wrong_direction(self):
        bbox_exts = [
            Port(name="o_foo", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: o_foo
        """)

        with pytest.raises(InterfaceMappingError, match=r"has wrong direction"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_wrong_intf_mode(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: NOT_A_MODE
            signals:
              foo: i_foo
              bar: o_bar
        """)

        with pytest.raises(InterfaceMappingError, match=r"unknown interface mode"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_try_slice_bit(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo[0]
              bar: o_bar[1]
        """)

        with pytest.raises(InterfaceMappingError, match=r"Attempted to slice"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_wrong_port_name(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: o_foo
              bar: i_bar
        """)

        with pytest.raises(InterfaceMappingError, match=r"references non-existent port"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_try_select_field_bit(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo.what
              bar: o_bar
        """)

        with pytest.raises(InterfaceMappingError, match=r"Attempted to select field"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_try_select_missing_field(self):
        struct_with_one_bit = BitStruct(
            name="struct_with_one_bit",
            fields=[
                StructField(name="single_bit", type=Bit()),
            ],
        )

        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN, type=struct_with_one_bit),
            Port(name="o_bar", direction=PortDirection.OUT, type=struct_with_one_bit),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo.what
              bar: o_bar.single_bit
        """)

        with pytest.raises(InterfaceMappingError, match=r"is not a member of struct"):
            map_interfaces_to_module([mapping], [bbox_intf], bbox)

    def test_try_malformed_slice(self):
        with pytest.raises(ValidationError, match=r"Invalid bounds syntax"):
            InterfacePortMapping.from_yaml("""
            id:
              name: bbox
            interfaces:
              bbox:
                interface:
                  name: Blackbox
                mode: MANAGER
                signals:
                  foo: i_foo[1:2:3]
                  bar: o_bar
            """)

        with pytest.raises(ValidationError, match=r"Invalid bounds syntax"):
            InterfacePortMapping.from_yaml("""
            id:
              name: bbox
            interfaces:
              bbox:
                interface:
                  name: Blackbox
                mode: MANAGER
                signals:
                  foo: i_foo[1;2]
                  bar: o_bar
            """)

    def test_apply_mapping_twice(self):
        bbox_exts = [
            Port(name="i_foo", direction=PortDirection.IN),
            Port(name="o_bar", direction=PortDirection.OUT),
        ]
        bbox = Module(
            id=Identifier(name="bbox"),
            ports=bbox_exts,
            design=Design(),
        )

        mapping = InterfacePortMapping.from_yaml("""
        id:
          name: bbox
        interfaces:
          bbox:
            interface:
              name: Blackbox
            mode: MANAGER
            signals:
              foo: i_foo
              bar: o_bar
        """)

        map_interfaces_to_module([mapping], [bbox_intf], bbox)
        map_interfaces_to_module([mapping], [bbox_intf], bbox)

        assert len(bbox.interfaces) == 1

        root = bbox.interfaces.find_by_name_or_error("bbox")

        assert root.definition == bbox_intf
        assert root.mode == InterfaceMode.MANAGER

        root_used_ports = {x.io.name if x else "?" for _, x in root.signals.items()}
        assert root_used_ports == {"i_foo", "o_bar"}
