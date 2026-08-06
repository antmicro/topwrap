# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT, bv

dupl_prefix_exts = [
    Port(name="clk_i", direction=IN),
    Port(name="rst_ni", direction=IN),
    Port(name="memory_axi_ar_araddr", direction=IN, type=bv(32)),
    Port(name="memory_axi_ar_arburst", direction=IN, type=bv(2)),
    Port(name="memory_axi_ar_arsize", direction=IN, type=bv(3)),
    Port(name="memory_axi_ar_arlen", direction=IN, type=bv(8)),
    Port(name="memory_axi_ar_aruser", direction=IN, type=bv(4)),
    Port(name="memory_axi_ar_arid", direction=IN, type=bv(4)),
    Port(name="memory_axi_ar_arlock", direction=IN),
    Port(name="memory_axi_ar_arvalid", direction=IN),
    Port(name="memory_axi_ar_arready", direction=OUT),
    Port(name="memory_axi_r_rdata", direction=OUT, type=bv(64)),
    Port(name="memory_axi_r_rresp", direction=OUT, type=bv(2)),
    Port(name="memory_axi_r_rid", direction=OUT, type=bv(4)),
    Port(name="memory_axi_r_ruser", direction=OUT, type=bv(4)),
    Port(name="memory_axi_r_rlast", direction=OUT),
    Port(name="memory_axi_r_rvalid", direction=OUT),
    Port(name="memory_axi_r_rready", direction=IN),
    Port(name="memory_axi_aw_awaddr", direction=IN, type=bv(32)),
    Port(name="memory_axi_aw_awburst", direction=IN, type=bv(2)),
    Port(name="memory_axi_aw_awsize", direction=IN, type=bv(3)),
    Port(name="memory_axi_aw_awlen", direction=IN, type=bv(8)),
    Port(name="memory_axi_aw_awuser", direction=IN, type=bv(4)),
    Port(name="memory_axi_aw_awid", direction=IN, type=bv(4)),
    Port(name="memory_axi_aw_awlock", direction=IN),
    Port(name="memory_axi_aw_awvalid", direction=IN),
    Port(name="memory_axi_aw_awready", direction=OUT),
    Port(name="memory_axi_w_wdata", direction=IN, type=bv(64)),
    Port(name="memory_axi_w_wstrb", direction=IN, type=bv(8)),
    Port(name="memory_axi_w_wuser", direction=IN, type=bv(4)),
    Port(name="memory_axi_w_wlast", direction=IN),
    Port(name="memory_axi_w_wvalid", direction=IN),
    Port(name="memory_axi_w_wready", direction=OUT),
    Port(name="memory_axi_b_bresp", direction=OUT, type=bv(2)),
    Port(name="memory_axi_b_bid", direction=OUT, type=bv(4)),
    Port(name="memory_axi_b_buser", direction=OUT, type=bv(4)),
    Port(name="memory_axi_b_bvalid", direction=OUT),
    Port(name="memory_axi_b_bready", direction=IN),
]


dupl_prefix = Module(
    id=Identifier(
        name="dupl_prefix",
        library="regression",
    ),
    ports=dupl_prefix_exts,
    design=Design(),
)
