# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.hdl_types import (
    Bit,
    BitStruct,
    StructField,
)

from .util import bv

pulp_axi_aw_chan = BitStruct(
    name="axi_aw_chan",
    fields=[
        StructField(name="id", type=bv(3)),
        StructField(name="addr", type=bv(32)),
        StructField(name="len", type=bv(8)),
        StructField(name="size", type=bv(3)),
        StructField(name="burst", type=bv(2)),
        StructField(name="lock", type=Bit()),
        StructField(name="cache", type=bv(4)),
        StructField(name="prot", type=bv(3)),
        StructField(name="qos", type=bv(4)),
        StructField(name="region", type=bv(4)),
        StructField(name="atop", type=bv(4)),
    ],
)

pulp_axi_w_chan = BitStruct(
    name="axi_w_chan",
    fields=[
        StructField(name="data", type=bv(64)),
        StructField(name="strb", type=bv(8)),
        StructField(name="last", type=Bit()),
    ],
)

pulp_axi_b_chan = BitStruct(
    name="axi_b_chan",
    fields=[
        StructField(name="id", type=bv(3)),
        StructField(name="resp", type=bv(2)),
    ],
)

pulp_axi_ar_chan = BitStruct(
    name="axi_ar_chan",
    fields=[
        StructField(name="id", type=bv(3)),
        StructField(name="addr", type=bv(32)),
        StructField(name="len", type=bv(8)),
        StructField(name="size", type=bv(3)),
        StructField(name="burst", type=bv(2)),
        StructField(name="lock", type=Bit()),
        StructField(name="cache", type=bv(4)),
        StructField(name="prot", type=bv(3)),
        StructField(name="qos", type=bv(4)),
        StructField(name="region", type=bv(4)),
        StructField(name="atop", type=bv(4)),
        StructField(name="user", type=bv(4)),
    ],
)

pulp_axi_r_chan = BitStruct(
    name="axi_b_chan",
    fields=[
        StructField(name="id", type=bv(3)),
        StructField(name="data", type=bv(64)),
        StructField(name="resp", type=bv(2)),
        StructField(name="last", type=Bit()),
    ],
)

pulp_axi_req = BitStruct(
    name="axi_req",
    fields=[
        StructField(name="aw", type=pulp_axi_aw_chan),
        StructField(name="aw_valid", type=Bit()),
        StructField(name="w", type=pulp_axi_w_chan),
        StructField(name="w_valid", type=Bit()),
        StructField(name="b_ready", type=Bit()),
        StructField(name="ar", type=pulp_axi_ar_chan),
        StructField(name="ar_valid", type=Bit()),
        StructField(name="r_ready", type=Bit()),
    ],
)

pulp_axi_resp = BitStruct(
    name="axi_resp",
    fields=[
        StructField(name="aw_ready", type=Bit()),
        StructField(name="w_ready", type=Bit()),
        StructField(name="b", type=pulp_axi_b_chan),
        StructField(name="b_valid", type=Bit()),
        StructField(name="ar_ready", type=Bit()),
        StructField(name="r", type=pulp_axi_r_chan),
        StructField(name="r_valid", type=Bit()),
    ],
)
