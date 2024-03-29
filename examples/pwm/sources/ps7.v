// Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0
module ps7_inst (
    output         FCLK0, // slice FCLK
    output [ 3: 0] FCLK_RESET0_N,
    input          MAXIGP0ACLK,
    output [31: 0] MAXIGP0ARADDR,
    output [ 1: 0] MAXIGP0ARBURST,
    output [ 3: 0] MAXIGP0ARCACHE,
    output         MAXIGP0ARESETN,
    output [11: 0] MAXIGP0ARID,
    output [ 3: 0] MAXIGP0ARLEN,
    output [ 1: 0] MAXIGP0ARLOCK,
    output [ 2: 0] MAXIGP0ARPROT,
    output [ 3: 0] MAXIGP0ARQOS,
    input          MAXIGP0ARREADY,
    output [ 1: 0] MAXIGP0ARSIZE,
    output         MAXIGP0ARVALID,
    output [31: 0] MAXIGP0AWADDR,
    output [ 1: 0] MAXIGP0AWBURST,
    output [ 3: 0] MAXIGP0AWCACHE,
    output [11: 0] MAXIGP0AWID,
    output [ 3: 0] MAXIGP0AWLEN,
    output [ 1: 0] MAXIGP0AWLOCK,
    output [ 2: 0] MAXIGP0AWPROT,
    output [ 3: 0] MAXIGP0AWQOS,
    input          MAXIGP0AWREADY,
    output [ 1: 0] MAXIGP0AWSIZE,
    output         MAXIGP0AWVALID,
    input  [11: 0] MAXIGP0BID,
    output         MAXIGP0BREADY,
    input  [ 1: 0] MAXIGP0BRESP,
    input          MAXIGP0BVALID,
    input  [31: 0] MAXIGP0RDATA,
    input  [11: 0] MAXIGP0RID,
    input          MAXIGP0RLAST,
    output         MAXIGP0RREADY,
    input  [ 1: 0] MAXIGP0RRESP,
    input          MAXIGP0RVALID,
    output [31: 0] MAXIGP0WDATA,
    output [11: 0] MAXIGP0WID,
    output         MAXIGP0WLAST,
    input          MAXIGP0WREADY,
    output [ 3: 0] MAXIGP0WSTRB,
    output         MAXIGP0WVALID
);
    wire [ 3: 0] FCLK;

    assign FCLK0 = FCLK[0];

    PS7 ps7 (
    .FCLKCLK                  (FCLK),
    .FCLKRESETN               (FCLK_RESET0_N),
    .MAXIGP0ACLK              (MAXIGP0ACLK),
    .MAXIGP0ARADDR            (MAXIGP0ARADDR),
    .MAXIGP0ARBURST           (MAXIGP0ARBURST),
    .MAXIGP0ARCACHE           (MAXIGP0ARCACHE),
    .MAXIGP0ARESETN           (MAXIGP0ARESETN),
    .MAXIGP0ARID              (MAXIGP0ARID),
    .MAXIGP0ARLEN             (MAXIGP0ARLEN),
    .MAXIGP0ARLOCK            (MAXIGP0ARLOCK),
    .MAXIGP0ARPROT            (MAXIGP0ARPROT),
    .MAXIGP0ARQOS             (MAXIGP0ARQOS),
    .MAXIGP0ARREADY           (MAXIGP0ARREADY),
    .MAXIGP0ARSIZE            (MAXIGP0ARSIZE),
    .MAXIGP0ARVALID           (MAXIGP0ARVALID),
    .MAXIGP0AWADDR            (MAXIGP0AWADDR),
    .MAXIGP0AWBURST           (MAXIGP0AWBURST),
    .MAXIGP0AWCACHE           (MAXIGP0AWCACHE),
    .MAXIGP0AWID              (MAXIGP0AWID),
    .MAXIGP0AWLEN             (MAXIGP0AWLEN),
    .MAXIGP0AWLOCK            (MAXIGP0AWLOCK),
    .MAXIGP0AWPROT            (MAXIGP0AWPROT),
    .MAXIGP0AWQOS             (MAXIGP0AWQOS),
    .MAXIGP0AWREADY           (MAXIGP0AWREADY),
    .MAXIGP0AWSIZE            (MAXIGP0AWSIZE),
    .MAXIGP0AWVALID           (MAXIGP0AWVALID),
    .MAXIGP0BID               (MAXIGP0BID),
    .MAXIGP0BREADY            (MAXIGP0BREADY),
    .MAXIGP0BRESP             (MAXIGP0BRESP),
    .MAXIGP0BVALID            (MAXIGP0BVALID),
    .MAXIGP0RDATA             (MAXIGP0RDATA),
    .MAXIGP0RID               (MAXIGP0RID),
    .MAXIGP0RLAST             (MAXIGP0RLAST),
    .MAXIGP0RREADY            (MAXIGP0RREADY),
    .MAXIGP0RRESP             (MAXIGP0RRESP),
    .MAXIGP0RVALID            (MAXIGP0RVALID),
    .MAXIGP0WDATA             (MAXIGP0WDATA),
    .MAXIGP0WID               (MAXIGP0WID),
    .MAXIGP0WLAST             (MAXIGP0WLAST),
    .MAXIGP0WREADY            (MAXIGP0WREADY),
    .MAXIGP0WSTRB             (MAXIGP0WSTRB),
    .MAXIGP0WVALID            (MAXIGP0WVALID)
    );

endmodule
