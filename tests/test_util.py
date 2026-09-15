# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.util import (
    is_simple_sv_literal,
    parse_incdirs,
    parse_params,
    removeprefix,
    unwrap_simple_parenthesized_sv_literal,
)


def test_removeprefix():
    assert removeprefix("someprefixababa", "someprefix") == "ababa"
    assert removeprefix("", "abc") == ""
    assert removeprefix("abc", "") == "abc"
    assert removeprefix("", "") == ""


def test_simple_sv_literal_helpers():
    assert is_simple_sv_literal("0")
    assert is_simple_sv_literal("8'hFF")
    assert is_simple_sv_literal("'0")
    assert not is_simple_sv_literal("foo")

    assert unwrap_simple_parenthesized_sv_literal("(0)") == "0"
    assert unwrap_simple_parenthesized_sv_literal(" ( 8'hFF ) ") == "8'hFF"
    assert unwrap_simple_parenthesized_sv_literal("(foo)") == "(foo)"


def test_parse_params():
    assert parse_params("+incdir+", "+incdir+tests/hdl") == ["tests/hdl"]
    assert parse_params("+incdir+", "+incdir+first+second") == ["first", "second"]


def test_parse_incdirs():
    assert parse_incdirs(("source.sv", "+incdir+first+second")) == ["first", "second"]
    assert parse_incdirs(("source.sv",)) == []
