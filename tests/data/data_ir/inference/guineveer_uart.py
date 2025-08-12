# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT, bv

uart_exts = [
    Port(name="clk", direction=IN),
    Port(name="rst_l", direction=IN),
    Port(name="haddr_i", direction=IN, type=bv(64)),
    Port(name="hwdata_i", direction=IN, type=bv(32)),
    Port(name="hsel_i", direction=IN),
    Port(name="hwrite_i", direction=IN),
    Port(name="hready_i", direction=IN),
    Port(name="htrans_i", direction=IN, type=bv(2)),
    Port(name="hsize_i", direction=IN, type=bv(3)),
    Port(name="hresp_o", direction=OUT),
    Port(name="hreadyout_o", direction=OUT),
    Port(name="hrdata_o", direction=OUT, type=bv(32)),
]

uart = Module(
    id=Identifier(
        name="uart",
        library="guineveer",
    ),
    ports=uart_exts,
    design=Design(),
)
