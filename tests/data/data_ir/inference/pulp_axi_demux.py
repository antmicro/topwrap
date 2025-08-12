# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from tests.data.data_ir.inference.pulp_types import pulp_axi_req, pulp_axi_resp
from topwrap.model.connections import Port
from topwrap.model.design import Design
from topwrap.model.hdl_types import Dimensions, LogicArray
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from .util import IN, OUT

axi_demux_exts = [
    Port(name="clk_i", direction=IN),
    Port(name="rst_ni", direction=IN),
    Port(name="slv_req_i", direction=IN, type=pulp_axi_req),
    Port(name="slv_resp_o", direction=OUT, type=pulp_axi_resp),
    Port(
        name="mst_reqs_o",
        direction=OUT,
        type=LogicArray(
            name="mst_reqs",
            dimensions=[Dimensions(upper=ElaboratableValue(3))],
            item=pulp_axi_req,
        ),
    ),
    Port(
        name="mst_resps_i",
        direction=IN,
        type=LogicArray(
            name="mst_resps",
            dimensions=[Dimensions(upper=ElaboratableValue(3))],
            item=pulp_axi_resp,
        ),
    ),
]


axi_demux = Module(
    id=Identifier(
        name="axi_demux",
        library="guineveer",
    ),
    ports=axi_demux_exts,
    design=Design(),
)
