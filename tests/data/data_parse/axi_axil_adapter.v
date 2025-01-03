/*

Copyright (c) 2019 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

*/

// Language: Verilog 2001

`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * AXI4 to AXI4-Lite adapter
 */
module axi_axil_adapter #
(
    // Width of address bus in bits
    parameter ADDR_WIDTH = 32,
    // Width of input (subordinate) AXI interface data bus in bits
    parameter AXI_DATA_WIDTH = 32,
    // Width of input (subordinate) AXI interface wstrb (width of data bus in words)
    parameter AXI_STRB_WIDTH = (AXI_DATA_WIDTH/8),
    // Width of AXI ID signal
    parameter AXI_ID_WIDTH = 8,
    // Width of output (manager) AXI lite interface data bus in bits
    parameter AXIL_DATA_WIDTH = 32,
    // Width of output (manager) AXI lite interface wstrb (width of data bus in words)
    parameter AXIL_STRB_WIDTH = (AXIL_DATA_WIDTH/8),
    // When adapting to a wider bus, re-pack full-width burst instead of passing through narrow burst if possible
    parameter CONVERT_BURST = 1,
    // When adapting to a wider bus, re-pack all bursts instead of passing through narrow burst if possible
    parameter CONVERT_NARROW_BURST = 0
)
(
    input  wire                        clk,
    input  wire                        rst,

    /*
     * AXI subordinate interface
     */
    (* interface="axi_subordinate" *)
    input  wire [AXI_ID_WIDTH-1:0]     s_axi_awid,
    (* interface="axi_subordinate" *)
    input  wire [ADDR_WIDTH-1:0]       s_axi_awaddr,
    (* interface="axi_subordinate" *)
    input  wire [7:0]                  s_axi_awlen,
    (* interface="axi_subordinate" *)
    input  wire [2:0]                  s_axi_awsize,
    (* interface="axi_subordinate" *)
    input  wire [1:0]                  s_axi_awburst,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_awlock,
    (* interface="axi_subordinate" *)
    input  wire [3:0]                  s_axi_awcache,
    (* interface="axi_subordinate" *)
    input  wire [2:0]                  s_axi_awprot,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_awvalid,
    (* interface="axi_subordinate" *)
    output wire                        s_axi_awready,
    (* interface="axi_subordinate" *)
    input  wire [AXI_DATA_WIDTH-1:0]   s_axi_wdata,
    (* interface="axi_subordinate" *)
    input  wire [AXI_STRB_WIDTH-1:0]   s_axi_wstrb,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_wlast,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_wvalid,
    (* interface="axi_subordinate" *)
    output wire                        s_axi_wready,
    (* interface="axi_subordinate" *)
    output wire [AXI_ID_WIDTH-1:0]     s_axi_bid,
    (* interface="axi_subordinate" *)
    output wire [1:0]                  s_axi_bresp,
    (* interface="axi_subordinate" *)
    output wire                        s_axi_bvalid,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_bready,
    (* interface="axi_subordinate" *)
    input  wire [AXI_ID_WIDTH-1:0]     s_axi_arid,
    (* interface="axi_subordinate" *)
    input  wire [ADDR_WIDTH-1:0]       s_axi_araddr,
    (* interface="axi_subordinate" *)
    input  wire [7:0]                  s_axi_arlen,
    (* interface="axi_subordinate" *)
    input  wire [2:0]                  s_axi_arsize,
    (* interface="axi_subordinate" *)
    input  wire [1:0]                  s_axi_arburst,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_arlock,
    (* interface="axi_subordinate" *)
    input  wire [3:0]                  s_axi_arcache,
    (* interface="axi_subordinate" *)
    input  wire [2:0]                  s_axi_arprot,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_arvalid,
    (* interface="axi_subordinate" *)
    output wire                        s_axi_arready,
    (* interface="axi_subordinate" *)
    output wire [AXI_ID_WIDTH-1:0]     s_axi_rid,
    (* interface="axi_subordinate" *)
    output wire [AXI_DATA_WIDTH-1:0]   s_axi_rdata,
    (* interface="axi_subordinate" *)
    output wire [1:0]                  s_axi_rresp,
    (* interface="axi_subordinate" *)
    output wire                        s_axi_rlast,
    (* interface="axi_subordinate" *)
    output wire                        s_axi_rvalid,
    (* interface="axi_subordinate" *)
    input  wire                        s_axi_rready,

    /*
     * AXI lite manager interface
     */
    (* interface="axi_manager" *)
    output wire [ADDR_WIDTH-1:0]       m_axil_awaddr,
    (* interface="axi_manager" *)
    output wire [2:0]                  m_axil_awprot,
    (* interface="axi_manager" *)
    output wire                        m_axil_awvalid,
    (* interface="axi_manager" *)
    input  wire                        m_axil_awready,
    (* interface="axi_manager" *)
    output wire [AXIL_DATA_WIDTH-1:0]  m_axil_wdata,
    (* interface="axi_manager" *)
    output wire [AXIL_STRB_WIDTH-1:0]  m_axil_wstrb,
    (* interface="axi_manager" *)
    output wire                        m_axil_wvalid,
    (* interface="axi_manager" *)
    input  wire                        m_axil_wready,
    (* interface="axi_manager" *)
    input  wire [1:0]                  m_axil_bresp,
    (* interface="axi_manager" *)
    input  wire                        m_axil_bvalid,
    (* interface="axi_manager" *)
    output wire                        m_axil_bready,
    (* interface="axi_manager" *)
    output wire [ADDR_WIDTH-1:0]       m_axil_araddr,
    (* interface="axi_manager" *)
    output wire [2:0]                  m_axil_arprot,
    (* interface="axi_manager" *)
    output wire                        m_axil_arvalid,
    (* interface="axi_manager" *)
    input  wire                        m_axil_arready,
    (* interface="axi_manager" *)
    input  wire [AXIL_DATA_WIDTH-1:0]  m_axil_rdata,
    (* interface="axi_manager" *)
    input  wire [1:0]                  m_axil_rresp,
    (* interface="axi_manager" *)
    input  wire                        m_axil_rvalid,
    (* interface="axi_manager" *)
    output wire                        m_axil_rready
);


axi_axil_adapter_wr #(
    .ADDR_WIDTH(ADDR_WIDTH),
    .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
    .AXI_STRB_WIDTH(AXI_STRB_WIDTH),
    .AXI_ID_WIDTH(AXI_ID_WIDTH),
    .AXIL_DATA_WIDTH(AXIL_DATA_WIDTH),
    .AXIL_STRB_WIDTH(AXIL_STRB_WIDTH),
    .CONVERT_BURST(CONVERT_BURST),
    .CONVERT_NARROW_BURST(CONVERT_NARROW_BURST)
)
axi_axil_adapter_wr_inst (
    .clk(clk),
    .rst(rst),

    /*
     * AXI subordinate interface
     */
    .s_axi_awid(s_axi_awid),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awlen(s_axi_awlen),
    .s_axi_awsize(s_axi_awsize),
    .s_axi_awburst(s_axi_awburst),
    .s_axi_awlock(s_axi_awlock),
    .s_axi_awcache(s_axi_awcache),
    .s_axi_awprot(s_axi_awprot),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wlast(s_axi_wlast),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bid(s_axi_bid),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),

    /*
     * AXI lite manager interface
     */
    .m_axil_awaddr(m_axil_awaddr),
    .m_axil_awprot(m_axil_awprot),
    .m_axil_awvalid(m_axil_awvalid),
    .m_axil_awready(m_axil_awready),
    .m_axil_wdata(m_axil_wdata),
    .m_axil_wstrb(m_axil_wstrb),
    .m_axil_wvalid(m_axil_wvalid),
    .m_axil_wready(m_axil_wready),
    .m_axil_bresp(m_axil_bresp),
    .m_axil_bvalid(m_axil_bvalid),
    .m_axil_bready(m_axil_bready)
);

axi_axil_adapter_rd #(
    .ADDR_WIDTH(ADDR_WIDTH),
    .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
    .AXI_STRB_WIDTH(AXI_STRB_WIDTH),
    .AXI_ID_WIDTH(AXI_ID_WIDTH),
    .AXIL_DATA_WIDTH(AXIL_DATA_WIDTH),
    .AXIL_STRB_WIDTH(AXIL_STRB_WIDTH),
    .CONVERT_BURST(CONVERT_BURST),
    .CONVERT_NARROW_BURST(CONVERT_NARROW_BURST)
)
axi_axil_adapter_rd_inst (
    .clk(clk),
    .rst(rst),

    /*
     * AXI subordinate interface
     */
    .s_axi_arid(s_axi_arid),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_arlen(s_axi_arlen),
    .s_axi_arsize(s_axi_arsize),
    .s_axi_arburst(s_axi_arburst),
    .s_axi_arlock(s_axi_arlock),
    .s_axi_arcache(s_axi_arcache),
    .s_axi_arprot(s_axi_arprot),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_rid(s_axi_rid),
    .s_axi_rdata(s_axi_rdata),
    .s_axi_rresp(s_axi_rresp),
    .s_axi_rlast(s_axi_rlast),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),

    /*
     * AXI lite manager interface
     */
    .m_axil_araddr(m_axil_araddr),
    .m_axil_arprot(m_axil_arprot),
    .m_axil_arvalid(m_axil_arvalid),
    .m_axil_arready(m_axil_arready),
    .m_axil_rdata(m_axil_rdata),
    .m_axil_rresp(m_axil_rresp),
    .m_axil_rvalid(m_axil_rvalid),
    .m_axil_rready(m_axil_rready)
);

endmodule

`resetall
