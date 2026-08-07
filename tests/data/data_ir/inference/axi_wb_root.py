# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT, bv

axi_wb_root_exts = [
    Port(name="awaddr", direction=IN, type=bv(32)),
    Port(name="awid", direction=IN, type=bv(4)),
    Port(name="awprot", direction=IN, type=bv(3)),
    Port(name="awvalid", direction=IN),
    Port(name="awready", direction=OUT),
    Port(name="wdata", direction=IN, type=bv(64)),
    Port(name="wstrb", direction=IN, type=bv(8)),
    Port(name="wvalid", direction=IN),
    Port(name="wready", direction=OUT),
    Port(name="bresp", direction=OUT, type=bv(2)),
    Port(name="bid", direction=OUT, type=bv(4)),
    Port(name="bvalid", direction=OUT),
    Port(name="bready", direction=IN),
    Port(name="araddr", direction=IN, type=bv(32)),
    Port(name="arid", direction=IN, type=bv(4)),
    Port(name="arprot", direction=IN, type=bv(3)),
    Port(name="arvalid", direction=IN),
    Port(name="arready", direction=OUT),
    Port(name="rdata", direction=OUT, type=bv(64)),
    Port(name="rresp", direction=OUT, type=bv(2)),
    Port(name="rid", direction=OUT, type=bv(4)),
    Port(name="rvalid", direction=OUT),
    Port(name="rready", direction=IN),
    Port(name="cyc", direction=OUT),
    Port(name="stb", direction=OUT),
    Port(name="ack", direction=IN),
    Port(name="dat_w", direction=OUT, type=bv(32)),
    Port(name="dat_r", direction=IN, type=bv(32)),
    Port(name="adr", direction=OUT, type=bv(32)),
    Port(name="sel", direction=OUT, type=bv(4)),
    Port(name="we", direction=OUT),
    Port(name="lock", direction=OUT),
    Port(name="cti", direction=OUT, type=bv(3)),
    Port(name="bte", direction=OUT, type=bv(2)),
    Port(name="tgd_w", direction=OUT),
    Port(name="tgd_r", direction=IN),
    Port(name="tga", direction=OUT),
    Port(name="tgc", direction=OUT),
    Port(name="stall", direction=IN),
    Port(name="err", direction=IN),
    Port(name="rty", direction=IN),
]


axi_wb_root = Module(
    id=Identifier(
        name="axi_wb_root",
        library="regression",
    ),
    ports=axi_wb_root_exts,
    design=Design(),
)
