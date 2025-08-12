# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT, bv

i3c_exts = [
    Port(name="clk_i", direction=IN),
    Port(name="rst_ni", direction=IN),
    Port(name="araddr_i", direction=IN, type=bv(32)),
    Port(name="arburst_i", direction=IN, type=bv(2)),
    Port(name="arsize_i", direction=IN, type=bv(3)),
    Port(name="arlen_i", direction=IN, type=bv(8)),
    Port(name="aruser_i", direction=IN, type=bv(4)),
    Port(name="arid_i", direction=IN, type=bv(4)),
    Port(name="arlock_i", direction=IN),
    Port(name="arvalid_i", direction=IN),
    Port(name="arready_o", direction=OUT),
    Port(name="rdata_o", direction=OUT, type=bv(64)),
    Port(name="rresp_o", direction=OUT, type=bv(2)),
    Port(name="rid_o", direction=OUT, type=bv(4)),
    Port(name="ruser_o", direction=OUT, type=bv(4)),
    Port(name="rlast_o", direction=OUT),
    Port(name="rvalid_o", direction=OUT),
    Port(name="rready_i", direction=IN),
    Port(name="awaddr_i", direction=IN, type=bv(32)),
    Port(name="awburst_i", direction=IN, type=bv(2)),
    Port(name="awsize_i", direction=IN, type=bv(3)),
    Port(name="awlen_i", direction=IN, type=bv(8)),
    Port(name="awuser_i", direction=IN, type=bv(4)),
    Port(name="awid_i", direction=IN, type=bv(4)),
    Port(name="awlock_i", direction=IN),
    Port(name="awvalid_i", direction=IN),
    Port(name="awready_o", direction=OUT),
    Port(name="wdata_i", direction=IN, type=bv(64)),
    Port(name="wstrb_i", direction=IN, type=bv(8)),
    Port(name="wuser_i", direction=IN, type=bv(4)),
    Port(name="wlast_i", direction=IN),
    Port(name="wvalid_i", direction=IN),
    Port(name="wready_o", direction=OUT),
    Port(name="bresp_o", direction=OUT, type=bv(2)),
    Port(name="bid_o", direction=OUT, type=bv(4)),
    Port(name="buser_o", direction=OUT, type=bv(4)),
    Port(name="bvalid_o", direction=OUT),
    Port(name="bready_i", direction=IN),
]


i3c = Module(
    id=Identifier(
        name="i3c",
        library="guineveer",
    ),
    ports=i3c_exts,
    design=Design(),
)
