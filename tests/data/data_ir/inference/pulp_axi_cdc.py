# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from tests.data.data_ir.inference.pulp_types import pulp_axi_req, pulp_axi_resp
from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT

axi_cdc_exts = [
    Port(name="src_clk_i", direction=IN),
    Port(name="src_rst_ni", direction=IN),
    Port(name="src_req_i", direction=IN, type=pulp_axi_req),
    Port(name="src_resp_o", direction=OUT, type=pulp_axi_resp),
    Port(name="dst_clk_i", direction=IN),
    Port(name="dst_rst_ni", direction=IN),
    Port(name="dst_req_o", direction=OUT, type=pulp_axi_req),
    Port(name="dst_resp_i", direction=IN, type=pulp_axi_resp),
]


axi_cdc = Module(
    id=Identifier(
        name="axi_cdc",
        library="guineveer",
    ),
    ports=axi_cdc_exts,
    design=Design(),
)
