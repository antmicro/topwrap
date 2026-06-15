// Copyright (c) 2026 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

typedef struct packed {
    logic [5:0]  id;
    logic [31:0] addr;
    logic [7:0]  len;
    logic [2:0]  size;
    logic [1:0]  burst;
    logic        lock;
    logic [3:0]  cache;
    logic [2:0]  prot;
    logic [3:0]  qos;
    logic [3:0]  region;
    logic [5:0]  atop;
    logic        user;
} axi_aw_chan_t;

typedef struct packed {
    logic [63:0] data;
    logic [7:0]  strb;
    logic        last;
    logic        user;
} axi_w_chan_t;

typedef struct packed {
    logic [5:0] id;
    logic [1:0] resp;
    logic       user;
} axi_b_chan_t;

typedef struct packed {
    logic [5:0]  id;
    logic [31:0] addr;
    logic [7:0]  len;
    logic [2:0]  size;
    logic [1:0]  burst;
    logic        lock;
    logic [3:0]  cache;
    logic [2:0]  prot;
    logic [3:0]  qos;
    logic [3:0]  region;
    logic        user;
} axi_ar_chan_t;

typedef struct packed {
    logic [5:0]  id;
    logic [63:0] data;
    logic [1:0]  resp;
    logic        last;
    logic        user;
} axi_r_chan_t;

typedef struct packed {
    axi_aw_chan_t aw;
    logic         aw_valid;
    axi_w_chan_t  w;
    logic         w_valid;
    logic         b_ready;
    axi_ar_chan_t ar;
    logic         ar_valid;
    logic         r_ready;
} axi_req_t;

typedef struct packed {
    logic        aw_ready;
    logic        ar_ready;
    logic        w_ready;
    logic        b_valid;
    axi_b_chan_t b;
    logic        r_valid;
    axi_r_chan_t r;
} axi_resp_t;

module sram_wrapper (
    input wire clk_i,
    input wire rst_ni,
    input  axi_req_t  axi_req,
    output axi_resp_t axi_resp
);
endmodule
