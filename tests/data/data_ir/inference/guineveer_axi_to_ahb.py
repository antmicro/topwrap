# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT, bv

axi_to_ahb_exts = [
    Port(name="axi_awvalid", direction=IN),
    Port(name="axi_awready", direction=OUT),
    Port(name="axi_awid", direction=IN, type=bv(1)),
    Port(name="axi_awaddr", direction=IN, type=bv(32)),
    Port(name="axi_awsize", direction=IN, type=bv(3)),
    Port(name="axi_awprot", direction=IN, type=bv(3)),
    Port(name="axi_wvalid", direction=IN),
    Port(name="axi_wready", direction=OUT),
    Port(name="axi_wdata", direction=IN, type=bv(64)),
    Port(name="axi_wstrb", direction=IN, type=bv(8)),
    Port(name="axi_wlast", direction=IN),
    Port(name="axi_bvalid", direction=OUT),
    Port(name="axi_bready", direction=IN),
    Port(name="axi_bresp", direction=OUT, type=bv(2)),
    Port(name="axi_bid", direction=OUT, type=bv(1)),
    Port(name="axi_arvalid", direction=IN),
    Port(name="axi_arready", direction=OUT),
    Port(name="axi_arid", direction=IN, type=bv(1)),
    Port(name="axi_araddr", direction=IN, type=bv(32)),
    Port(name="axi_arsize", direction=IN, type=bv(3)),
    Port(name="axi_arprot", direction=IN, type=bv(3)),
    Port(name="axi_rvalid", direction=OUT),
    Port(name="axi_rready", direction=IN),
    Port(name="axi_rid", direction=OUT, type=bv(1)),
    Port(name="axi_rdata", direction=OUT, type=bv(64)),
    Port(name="axi_rresp", direction=OUT, type=bv(2)),
    Port(name="axi_rlast", direction=OUT),
    Port(name="ahb_haddr", direction=OUT, type=bv(32)),
    Port(name="ahb_hburst", direction=OUT, type=bv(3)),
    Port(name="ahb_hmastlock", direction=OUT),
    Port(name="ahb_hprot", direction=OUT, type=bv(4)),
    Port(name="ahb_hsize", direction=OUT, type=bv(3)),
    Port(name="ahb_htrans", direction=OUT, type=bv(2)),
    Port(name="ahb_hwrite", direction=OUT),
    Port(name="ahb_hwdata", direction=OUT, type=bv(64)),
    Port(name="ahb_hrdata", direction=IN, type=bv(64)),
    Port(name="ahb_hready", direction=IN),
    Port(name="ahb_hresp", direction=IN),
]

axi_to_ahb = Module(
    id=Identifier(
        name="axi_to_ahb",
        library="guineveer",
    ),
    ports=axi_to_ahb_exts,
    design=Design(),
)
