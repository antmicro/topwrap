# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.util import removeprefix


def test_removeprefix():
    assert removeprefix("someprefixababa", "someprefix") == "ababa"
    assert removeprefix("", "abc") == ""
    assert removeprefix("abc", "") == "abc"
    assert removeprefix("", "") == ""
