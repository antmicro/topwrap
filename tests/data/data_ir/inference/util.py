# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Optional

from examples.ir_examples.advanced.ir.types import make_mm
from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    Dimensions,
    ElaboratableValue,
)
from topwrap.model.interface import InterfaceSignal


def bv(width: int) -> Bits:
    return Bits(dimensions=[Dimensions(upper=ElaboratableValue(width - 1))])


def sig(
    name: str,
    pattern: str,
    width: int,
    direction: PortDirection,
    *,
    mreq: bool = True,
    sreq: Optional[bool] = None,
    default: Optional[str] = None,
) -> InterfaceSignal:
    """
    Helper function to concisely define interface definition signals.

    :param name: Name of the signal.
    :param pattern: Regex pattern to match port names to signal.
    :param width: Bit width of signal.
    :param direction: Direction of the signal from the manager's perspective.
    :param mreq: Is signal required on manager side.
    :param sreq: Is signal required on subordinate side. None implies subordinate follows manager.
    :param default: Default value if nothing is connected to the signal. None implies no default.
    """

    return InterfaceSignal(
        name=name,
        regexp=re.compile(pattern),
        type=bv(width) if width > 1 else Bit(),
        modes=make_mm(mreq, direction, sreq),
        default=ElaboratableValue(default) if default else None,
    )


IN = PortDirection.IN
OUT = PortDirection.OUT
