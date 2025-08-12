# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier

from .util import IN, OUT, sig

bbox_intf = InterfaceDefinition(
    id=Identifier(name="Blackbox"),
    signals=[
        sig("foo", ".*?_?[Ff][Oo]{2}", 1, IN),
        sig("bar", ".*?_?[Bb][Aa][Rr]", 1, OUT),
    ],
)


bbox_full_intf = InterfaceDefinition(
    id=Identifier(name="BlackboxFull"),
    signals=[
        sig("foo", ".*?_?[Ff][Oo]{2}", 1, IN),
        sig("bar", ".*?_?[Bb][Aa][Rr]", 1, OUT),
        sig("baz", ".*?_?[Bb][Aa][Zz]", 1, OUT),
    ],
)


bbox_in_only_intf = InterfaceDefinition(
    id=Identifier(name="BlackboxInOnly"),
    signals=[
        sig("in1", "in1|IN1", 1, IN),
        sig("in2", "in2|IN2", 1, IN),
    ],
)
