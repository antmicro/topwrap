# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier

from .util import IN, OUT, sig

axi4lite_intf = InterfaceDefinition(
    id=Identifier(name="AXI4Lite"),
    signals=[
        # AW channel.
        sig("awaddr", "aw[._]?addr", 32, OUT),
        sig("awprot", "aw[._]?prot", 3, OUT, sreq=False),
        sig("awvalid", "aw[._]?valid", 1, OUT),
        sig("awready", "aw[._]?ready", 1, IN),
        # W channel.
        sig("wdata", "w[._]?data", 64, OUT),
        sig("wstrb", "w[._]?strb", 8, OUT, mreq=False, sreq=True, default="255"),
        sig("wvalid", "w[._]?valid", 1, OUT),
        sig("wready", "w[._]?ready", 1, IN),
        # B channel.
        sig("bresp", "b[._]?resp", 2, IN, mreq=False, sreq=True, default="0"),
        sig("bvalid", "b[._]?valid", 1, IN),
        sig("bready", "b[._]?ready", 1, OUT),
        # AR channel.
        sig("araddr", "ar[._]?addr", 32, OUT),
        sig("arprot", "ar[._]?prot", 3, OUT, sreq=False),
        sig("arvalid", "ar[._]?valid", 1, OUT),
        sig("arready", "ar[._]?ready", 1, IN),
        # R channel.
        sig("rdata", "r[._]?data", 64, IN),
        sig("rlast", "r[._]?last", 1, IN, mreq=False, sreq=True),
        sig("rvalid", "r[._]?valid", 1, IN),
        sig("rready", "r[._]?ready", 1, OUT),
    ],
)
