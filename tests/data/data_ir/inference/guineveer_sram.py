# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from tests.data.data_ir.inference.pulp_types import pulp_axi_req, pulp_axi_resp
from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .util import IN, OUT

sram_exts = [
    Port(name="clk_i", direction=IN),
    Port(name="rst_ni", direction=IN),
    Port(name="axi_req_i", direction=IN, type=pulp_axi_req),
    Port(name="axi_resp_o", direction=OUT, type=pulp_axi_resp),
]


sram = Module(
    id=Identifier(
        name="sram",
        library="guineveer",
    ),
    ports=sram_exts,
    design=Design(),
)
