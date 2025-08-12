# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re

from examples.ir_examples.advanced.ir.types import make_mm
from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import (
    Bit,
)
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceSignal,
)
from topwrap.model.misc import Identifier

bbox_intf = InterfaceDefinition(
    id=Identifier(name="Blackbox"),
    signals=[
        InterfaceSignal(
            name="foo",
            regexp=re.compile(".*?_?[Ff][Oo]{2}"),
            type=Bit(),
            modes=make_mm(True, PortDirection.IN),
        ),
        InterfaceSignal(
            name="bar",
            regexp=re.compile(".*?_?[Bb][Aa][Rr]"),
            type=Bit(),
            modes=make_mm(True, PortDirection.OUT),
        ),
    ],
)


bbox_full_intf = InterfaceDefinition(
    id=Identifier(name="BlackboxFull"),
    signals=[
        InterfaceSignal(
            name="foo",
            regexp=re.compile(".*?_?[Ff][Oo]{2}"),
            type=Bit(),
            modes=make_mm(True, PortDirection.IN),
        ),
        InterfaceSignal(
            name="bar",
            regexp=re.compile(".*?_?[Bb][Aa][Rr]"),
            type=Bit(),
            modes=make_mm(True, PortDirection.OUT),
        ),
        InterfaceSignal(
            name="baz",
            regexp=re.compile(".*?_?[Bb][Aa][Zz]"),
            type=Bit(),
            modes=make_mm(True, PortDirection.OUT),
        ),
    ],
)


bbox_in_only_intf = InterfaceDefinition(
    id=Identifier(name="BlackboxInOnly"),
    signals=[
        InterfaceSignal(
            name="in1",
            regexp=re.compile("in1|IN1"),
            type=Bit(),
            modes=make_mm(True, PortDirection.IN),
        ),
        InterfaceSignal(
            name="in2",
            regexp=re.compile("in2|IN2"),
            type=Bit(),
            modes=make_mm(True, PortDirection.IN),
        ),
    ],
)
