# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier

from .util import IN, OUT, sig

axi4_intf = InterfaceDefinition(
    id=Identifier(name="AXI4"),
    signals=[
        # AW channel.
        sig("awid", "aw[._]?id", 3, OUT, mreq=False, sreq=True, default="0"),
        sig("awaddr", "aw[._]?addr", 32, OUT),
        sig("awregion", "aw[._]?region", 4, OUT, mreq=False, default="0"),
        sig("awlen", "aw[._]?len", 8, OUT, mreq=False, sreq=True, default="0"),
        sig("awsize", "aw[._]?size", 3, OUT, mreq=False, sreq=True, default="3"),
        sig("awburst", "aw[._]?burst", 2, OUT, mreq=False, sreq=True, default="1"),
        sig("awlock", "aw[._]?lock", 1, OUT, mreq=False, default="0"),
        sig("awcache", "aw[._]?cache", 4, OUT, mreq=False, default="0"),
        sig("awprot", "aw[._]?prot", 3, OUT, sreq=False),
        sig("awqos", "aw[._]?qos", 4, OUT, mreq=False, default="0"),
        sig("awvalid", "aw[._]?valid", 1, OUT),
        sig("awready", "aw[._]?ready", 1, IN),
        # W channel.
        sig("wdata", "w[._]?data", 64, OUT),
        sig("wstrb", "w[._]?strb", 8, OUT, mreq=False, sreq=True, default="255"),
        sig("wlast", "w[._]?last", 1, OUT, sreq=False),
        sig("wvalid", "w[._]?valid", 1, OUT),
        sig("wready", "w[._]?ready", 1, IN),
        # B channel.
        sig("bid", "b[._]?id", 3, IN, mreq=False, sreq=True),
        sig("bresp", "b[._]?resp", 2, IN, mreq=False, sreq=True, default="0"),
        sig("bvalid", "b[._]?valid", 1, IN),
        sig("bready", "b[._]?ready", 1, OUT),
        # AR channel.
        sig("arid", "ar[._]?id", 3, OUT, mreq=False, sreq=True, default="0"),
        sig("araddr", "ar[._]?addr", 32, OUT),
        sig("arregion", "ar[._]?region", 4, OUT, mreq=False, default="0"),
        sig("arlen", "ar[._]?len", 8, OUT, mreq=False, sreq=True, default="0"),
        sig("arsize", "ar[._]?size", 3, OUT, mreq=False, sreq=True, default="3"),
        sig("arburst", "ar[._]?burst", 2, OUT, mreq=False, sreq=True, default="1"),
        sig("arlock", "ar[._]?lock", 1, OUT, mreq=False, default="0"),
        sig("arcache", "ar[._]?cache", 4, OUT, mreq=False, default="0"),
        sig("arprot", "ar[._]?prot", 3, OUT, sreq=False),
        sig("arqos", "ar[._]?qos", 4, OUT, mreq=False, default="0"),
        sig("arvalid", "ar[._]?valid", 1, OUT),
        sig("arready", "ar[._]?ready", 1, IN),
        # R channel.
        sig("rid", "r[._]?id", 3, IN, mreq=False, sreq=True),
        sig("rdata", "r[._]?data", 64, IN),
        sig("rresp", "r[._]?resp", 2, IN, mreq=False, sreq=True, default="0"),
        sig("rlast", "r[._]?last", 1, IN, mreq=False, sreq=True),
        sig("rvalid", "r[._]?valid", 1, IN),
        sig("rready", "r[._]?ready", 1, OUT),
    ],
)
