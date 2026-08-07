# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier

from .util import IN, OUT, sig

wb_intf = InterfaceDefinition(
    id=Identifier(name="Wishbone"),
    signals=[
        sig("adr", "adr", 32, OUT),
        sig("dat_w", "dat_w", 32, OUT),
        sig("dat_r", "dat_r", 32, IN),
        sig("sel", "sel", 4, OUT),
        sig("cyc", "cyc", 1, OUT),
        sig("stb", "stb", 1, OUT),
        sig("we", "we", 1, OUT),
        sig("ack", "ack", 1, IN),
        sig("err", "err", 1, IN, mreq=False),
        sig("rty", "rty", 1, IN, mreq=False),
        sig("stall", "stall", 1, IN, mreq=False),
        sig("lock", "lock", 1, OUT, mreq=False),
        sig("cti", "cti", 3, OUT, mreq=False),
        sig("bte", "bte", 2, OUT, mreq=False),
        sig("tgd_w", "tgd_w", 1, OUT, mreq=False),
        sig("tgd_r", "tgd_r", 1, IN, mreq=False),
        sig("tga", "tga", 1, OUT, mreq=False),
        sig("tgc", "tgc", 1, OUT, mreq=False),
    ],
)
