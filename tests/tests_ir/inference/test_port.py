# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


from typing import cast

import pytest

from tests.data.data_ir.inference.bbox_if import bbox_intf
from topwrap.model.connections import Port, PortDirection
from topwrap.model.design import Design
from topwrap.model.inference.port import (
    PortSelector,
    PortSelectorOp,
    PortSelectorOpT,
)
from topwrap.model.interface import (
    InterfaceMode,
)
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

TEST_SELECTORS_BASIC = [
    "foo",
    "foo.bar",
    "foo[1:0]",
    "foo.a.b",
    "foo.b[1].a[1:0][4:1]",
    "mst_reqs_o[2].ar.addr[3:0]",
]
TEST_SELECTORS_WHITESPACE = [
    "  foo     ",
    "foo . bar",
    "       foo [ 1 : 0 ] ",
    "  foo . a  . b ",
    "foo. b[1 ] . a[ 1: 0  ][  4 :  1   ]",
    "     mst_reqs_o  [   2 ] .  ar .  addr  [  3 :  0 ] ",
]
TEST_SELECTORS_PORTS = ["foo", "foo", "foo", "foo", "foo", "mst_reqs_o"]
TEST_SELECTORS_OPS = [
    (),
    ((PortSelectorOp.FIELD, "bar"),),
    ((PortSelectorOp.SLICE, (1, 0)),),
    ((PortSelectorOp.FIELD, "a"), (PortSelectorOp.FIELD, "b")),
    (
        (PortSelectorOp.FIELD, "b"),
        (PortSelectorOp.SLICE, (1, 1)),
        (PortSelectorOp.FIELD, "a"),
        (PortSelectorOp.SLICE, (1, 0)),
        (PortSelectorOp.SLICE, (4, 1)),
    ),
    (
        (PortSelectorOp.SLICE, (2, 2)),
        (PortSelectorOp.FIELD, "ar"),
        (PortSelectorOp.FIELD, "addr"),
        (PortSelectorOp.SLICE, (3, 0)),
    ),
]


class TestPortSelector:
    @pytest.mark.parametrize(
        "selector_str,port,ops", zip(TEST_SELECTORS_BASIC, TEST_SELECTORS_PORTS, TEST_SELECTORS_OPS)
    )
    def test_parse_basic(self, selector_str: str, port: str, ops: tuple[PortSelectorOpT, ...]):
        sel = PortSelector.from_str(selector_str)
        assert sel.port == port
        assert sel.ops == ops

    @pytest.mark.parametrize(
        "selector_str,port,ops",
        zip(TEST_SELECTORS_WHITESPACE, TEST_SELECTORS_PORTS, TEST_SELECTORS_OPS),
    )
    def test_parse_whitespace(self, selector_str: str, port: str, ops: tuple[PortSelectorOpT, ...]):
        sel = PortSelector.from_str(selector_str)
        assert sel.port == port
        assert sel.ops == ops

    @pytest.mark.parametrize(
        "selector_str",
        [
            "foo",
            "foo.bar",
            "foo[1:0]",
            "foo.a.b",
            "foo.b[1].a[1:0][4:0]",
            "mst_reqs_o[2].ar.addr[3:0]",
        ],
    )
    def test_to_str(self, selector_str: str):
        sel = PortSelector.from_str(selector_str)
        assert sel == PortSelector.from_str(str(sel))

    @pytest.mark.parametrize(
        "selector_str, error",
        [
            ("", "Empty port selector"),
            (".", "Empty module port name"),
            ("a.", "Empty field name"),
            ("a[]", "Invalid bounds syntax"),
            ("a[1:2:3]", "Invalid bounds syntax"),
            ("a[1:x]", "Invalid bounds syntax"),
            ("a[x:1]", "Invalid bounds syntax"),
            ("a[x;1]", "Invalid bounds syntax"),
            ("a[1;2]", "Invalid bounds syntax"),
            ("a[x]", "Invalid bounds syntax"),
            ("a[1]]", "Invalid bounds syntax"),
            ("a[[1]", "Invalid bounds syntax"),
            ("a[[1]]", "Invalid bounds syntax"),
        ],
    )
    def test_malformed(self, selector_str: str, error: str):
        with pytest.raises(ValueError, match=error):
            PortSelector.from_str(selector_str)

    def test_broken_op(self):
        sel = PortSelector("x", (cast(PortSelectorOpT, ("broken", "broken")),))

        with pytest.raises(RuntimeError, match="Invalid operation kind"):
            str(sel)

        with pytest.raises(RuntimeError, match="Invalid operation kind"):
            bbox_exts = [
                Port(name="x", direction=PortDirection.IN),
            ]
            bbox = Module(
                id=Identifier(name="bbox"),
                ports=bbox_exts,
                design=Design(),
            )
            sel.make_referenced_port(bbox, InterfaceMode.MANAGER, bbox_intf.signals[0])
