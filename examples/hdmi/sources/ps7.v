// Copyright (c) 2021 Antmicro
// SPDX-License-Identifier: Apache-2.0
module ps7_inst (
    inout  [14: 0] ddr_addr,
    inout  [ 2: 0] ddr_bankaddr,
    inout          ddr_cas_n,
    inout          ddr_cke,
    inout          ddr_clk_n,
    inout          ddr_clk,
    inout          ddr_cs_n,
    inout  [ 3: 0] ddr_dm,
    inout  [31: 0] ddr_dq,
    inout  [ 3: 0] ddr_dqs,
    inout  [ 3: 0] ddr_dqs_n,
    inout          ddr_drstb,
    inout          ddr_odt,
    inout          ddr_ras_n,
    inout          ddr_vr_n,
    inout          ddr_vr,
    inout          ddr_web,
    inout  [53: 0] ps_mio,
    inout          ps_clk,
    inout          ps_porb,
    inout          ps_srstb,
    output         FCLK0, // slice FCLK
    output         FCLK1, // slice FCLK
    output [ 3: 0] FCLK_RESET0_N,
    input IRQ_F2P_0, // slice IRQF2P
    input IRQ_F2P_1, // slice IRQF2P
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
    output         MAXIGP0WVALID,
    input          SAXIHP0ACLK,
    input  [31: 0] SAXIHP0ARADDR,
    input  [ 1: 0] SAXIHP0ARBURST,
    input  [ 3: 0] SAXIHP0ARCACHE,
    output         SAXIHP0ARESETN,
    input  [ 5: 0] SAXIHP0ARID,
    input  [ 3: 0] SAXIHP0ARLEN,
    input  [ 1: 0] SAXIHP0ARLOCK,
    input  [ 2: 0] SAXIHP0ARPROT,
    input  [ 3: 0] SAXIHP0ARQOS,
    output         SAXIHP0ARREADY,
    input  [ 1: 0] SAXIHP0ARSIZE,
    input          SAXIHP0ARVALID,
    input  [31: 0] SAXIHP0AWADDR,
    input  [ 1: 0] SAXIHP0AWBURST,
    input  [ 3: 0] SAXIHP0AWCACHE,
    input  [ 5: 0] SAXIHP0AWID,
    input  [ 3: 0] SAXIHP0AWLEN,
    input  [ 1: 0] SAXIHP0AWLOCK,
    input  [ 2: 0] SAXIHP0AWPROT,
    input  [ 3: 0] SAXIHP0AWQOS,
    output         SAXIHP0AWREADY,
    input  [ 1: 0] SAXIHP0AWSIZE,
    input          SAXIHP0AWVALID,
    output [ 5: 0] SAXIHP0BID,
    input          SAXIHP0BREADY,
    output [ 1: 0] SAXIHP0BRESP,
    output         SAXIHP0BVALID,
    output [ 2: 0] SAXIHP0RACOUNT,
    output [ 7: 0] SAXIHP0RCOUNT,
    output [63: 0] SAXIHP0RDATA,
    input          SAXIHP0RDISSUECAP1EN,
    output [ 5: 0] SAXIHP0RID,
    output         SAXIHP0RLAST,
    input          SAXIHP0RREADY,
    output [ 1: 0] SAXIHP0RRESP,
    output         SAXIHP0RVALID,
    output [ 5: 0] SAXIHP0WACOUNT,
    output [ 7: 0] SAXIHP0WCOUNT,
    input  [63: 0] SAXIHP0WDATA,
    input  [ 5: 0] SAXIHP0WID,
    input          SAXIHP0WLAST,
    output         SAXIHP0WREADY,
    input          SAXIHP0WRISSUECAP1EN,
    input  [ 7: 0] SAXIHP0WSTRB,
    input          SAXIHP0WVALID
);
    wire [ 3: 0] FCLK;
    wire  [19: 0] IRQF2P;
    
    assign FCLK0 = FCLK[0];
    assign FCLK1 = FCLK[1];
    assign IRQF2P[0] = IRQ_F2P_0;
    assign IRQF2P[1] = IRQ_F2P_1;

    PS7 (
    .DDRA                     (ddr_addr),
    .DDRBA                    (ddr_bankaddr),
    .DDRCASB                  (ddr_cas_n),
    .DDRCKE                   (ddr_cke),
    .DDRCKN                   (ddr_clk_n),
    .DDRCKP                   (ddr_clk),
    .DDRCSB                   (ddr_cs_n),
    .DDRDM                    (ddr_dm),
    .DDRDQ                    (ddr_dq),
    .DDRDQSP                  (ddr_dqs),
    .DDRDQSN                  (ddr_dqs_n),
    .DDRDRSTB                 (ddr_drstb),
    .DDRODT                   (ddr_odt),
    .DDRRASB                  (ddr_ras_n),
    .DDRVRN                   (ddr_vr_n),
    .DDRVRP                   (ddr_vr),
    .DDRWEB                   (ddr_web),
    .DDRARB                   (0),
    .DMA0ACLK                 (0),
    .DMA0DAREADY              (0),
    .DMA0DAVALID              (0),
    .DMA0DRLAST               (0),
    .DMA0DRTYPE               (0),
    .DMA0DRVALID              (0),
    .DMA1ACLK                 (0),
    .DMA1DAREADY              (0),
    .DMA1DRLAST               (0),
    .DMA1DRTYPE               (0),
    .DMA1DRVALID              (0),
    .DMA2ACLK                 (0),
    .DMA2DAREADY              (0),
    .DMA2DRLAST               (0),
    .DMA2DRTYPE               (0),
    .DMA2DRVALID              (0),
    .DMA3ACLK                 (0),
    .DMA3DAREADY              (0),
    .DMA3DRLAST               (0),
    .DMA3DRTYPE               (0),
    .DMA3DRVALID              (0),
    .EMIOCAN0PHYRX            (0),
    .EMIOCAN1PHYRX            (0),
    .EMIOENET0EXTINTIN        (0),
    .EMIOENET0GMIICOL         (0),
    .EMIOENET0GMIICRS         (0),
    .EMIOENET0GMIIRXCLK       (0),
    .EMIOENET0GMIIRXD         (0),
    .EMIOENET0GMIIRXDV        (0),
    .EMIOENET0GMIIRXER        (0),
    .EMIOENET0GMIITXCLK       (0),
    .EMIOENET0MDIOI           (0),
    .EMIOENET1EXTINTIN        (0),
    .EMIOENET1GMIICOL         (0),
    .EMIOENET1GMIICRS         (0),
    .EMIOENET1GMIIRXCLK       (0),
    .EMIOENET1GMIIRXD         (0),
    .EMIOENET1GMIIRXDV        (0),
    .EMIOENET1GMIIRXER        (0),
    .EMIOENET1GMIITXCLK       (0),
    .EMIOENET1MDIOI           (0),
    .EMIOGPIOI                (0),
    .EMIOI2C0SCLI             (0),
    .EMIOI2C0SDAI             (0),
    .EMIOI2C1SCLI             (0),
    .EMIOI2C1SDAI             (0),
    .EMIOPJTAGTCK             (0),
    .EMIOPJTAGTDI             (0),
    .EMIOPJTAGTMS             (0),
    .EMIOSDIO0CDN             (0),
    .EMIOSDIO0CLKFB           (0),
    .EMIOSDIO0CMDI            (0),
    .EMIOSDIO0DATAI           (0),
    .EMIOSDIO0WP              (0),
    .EMIOSDIO1CDN             (0),
    .EMIOSDIO1CLKFB           (0),
    .EMIOSDIO1CMDI            (0),
    .EMIOSDIO1DATAI           (0),
    .EMIOSDIO1WP              (0),
    .EMIOSPI0MI               (0),
    .EMIOSPI0SCLKI            (0),
    .EMIOSPI0SI               (0),
    .EMIOSPI0SSIN             (0),
    .EMIOSPI1MI               (0),
    .EMIOSPI1SCLKI            (0),
    .EMIOSPI1SI               (0),
    .EMIOSPI1SSIN             (0),
    .EMIOSRAMINTIN            (0),
    .EMIOTRACECLK             (0),
    .EMIOTTC0CLKI             (0),
    .EMIOTTC1CLKI             (0),
    .EMIOUART0CTSN            (0),
    .EMIOUART0DCDN            (0),
    .EMIOUART0DSRN            (0),
    .EMIOUART0RIN             (0),
    .EMIOUART0RX              (0),
    .EMIOUART1CTSN            (0),
    .EMIOUART1DCDN            (0),
    .EMIOUART1DSRN            (0),
    .EMIOUART1RIN             (0),
    .EMIOUART1RX              (0),
    .EMIOUSB0VBUSPWRFAULT     (0),
    .EMIOUSB1VBUSPWRFAULT     (0),
    .EMIOWDTCLKI              (0),
    .EVENTEVENTI              (0),
    .FCLKCLKTRIGN             (0),
    .FPGAIDLEN                (0),
    .FTMDTRACEINATID          (0),
    .FTMDTRACEINCLOCK         (0),
    .FTMDTRACEINDATA          (0),
    .FTMDTRACEINVALID         (0),
    .FTMTF2PDEBUG             (0),
    .FTMTF2PTRIG              (0),
    .FTMTP2FTRIGACK           (0),
    .MAXIGP1ACLK              (0),
    .MAXIGP1ARREADY           (0),
    .MAXIGP1AWREADY           (0),
    .MAXIGP1BID               (0),
    .MAXIGP1BRESP             (0),
    .MAXIGP1BVALID            (0),
    .MAXIGP1RDATA             (0),
    .MAXIGP1RID               (0),
    .MAXIGP1RLAST             (0),
    .MAXIGP1RRESP             (0),
    .MAXIGP1RVALID            (0),
    .MAXIGP1WREADY            (0),
    .SAXIACPACLK	      (0),
    .SAXIACPARADDR	      (0),
    .SAXIACPARBURST	      (0),
    .SAXIACPARCACHE	      (0),
    .SAXIACPARID	      (0),
    .SAXIACPARLEN	      (0),
    .SAXIACPARLOCK	      (0),
    .SAXIACPARPROT	      (0),
    .SAXIACPARQOS	      (0),
    .SAXIACPARSIZE	      (0),
    .SAXIACPARUSER	      (0),
    .SAXIACPARVALID	      (0),
    .SAXIACPAWADDR	      (0),
    .SAXIACPAWBURST	      (0),
    .SAXIACPAWCACHE	      (0),
    .SAXIACPAWID	      (0),
    .SAXIACPAWLEN	      (0),
    .SAXIACPAWLOCK	      (0),
    .SAXIACPAWPROT	      (0),
    .SAXIACPAWQOS	      (0),
    .SAXIACPAWSIZE	      (0),
    .SAXIACPAWUSER	      (0),
    .SAXIACPAWVALID	      (0),
    .SAXIACPBREADY	      (0),
    .SAXIACPRREADY	      (0),
    .SAXIACPWDATA	      (0),
    .SAXIACPWID	              (0),
    .SAXIACPWLAST	      (0),
    .SAXIACPWSTRB	      (0),
    .SAXIACPWVALID	      (0),
    .SAXIGP0ACLK	      (0),
    .SAXIGP0ARADDR	      (0),
    .SAXIGP0ARBURST	      (0),
    .SAXIGP0ARCACHE	      (0),
    .SAXIGP0ARID	      (0),
    .SAXIGP0ARLEN	      (0),
    .SAXIGP0ARLOCK	      (0),
    .SAXIGP0ARPROT	      (0),
    .SAXIGP0ARQOS	      (0),
    .SAXIGP0ARSIZE	      (0),
    .SAXIGP0ARVALID	      (0),
    .SAXIGP0AWADDR	      (0),
    .SAXIGP0AWBURST	      (0),
    .SAXIGP0AWCACHE	      (0),
    .SAXIGP0AWID	      (0),
    .SAXIGP0AWLEN	      (0),
    .SAXIGP0AWLOCK	      (0),
    .SAXIGP0AWPROT	      (0),
    .SAXIGP0AWQOS	      (0),
    .SAXIGP0AWSIZE	      (0),
    .SAXIGP0AWVALID	      (0),
    .SAXIGP0BREADY	      (0),
    .SAXIGP0RREADY	      (0),
    .SAXIGP0WDATA	      (0),
    .SAXIGP0WID	              (0),
    .SAXIGP0WLAST	      (0),
    .SAXIGP0WSTRB	      (0),
    .SAXIGP0WVALID	      (0),
    .SAXIGP1ACLK	      (0),
    .SAXIGP1ARADDR	      (0),
    .SAXIGP1ARBURST	      (0),
    .SAXIGP1ARCACHE	      (0),
    .SAXIGP1ARID	      (0),
    .SAXIGP1ARLEN	      (0),
    .SAXIGP1ARLOCK	      (0),
    .SAXIGP1ARPROT	      (0),
    .SAXIGP1ARQOS	      (0),
    .SAXIGP1ARSIZE	      (0),
    .SAXIGP1ARVALID	      (0),
    .SAXIGP1AWADDR	      (0),
    .SAXIGP1AWBURST	      (0),
    .SAXIGP1AWCACHE	      (0),
    .SAXIGP1AWID	      (0),
    .SAXIGP1AWLEN	      (0),
    .SAXIGP1AWLOCK	      (0),
    .SAXIGP1AWPROT	      (0),
    .SAXIGP1AWQOS	      (0),
    .SAXIGP1AWSIZE	      (0),
    .SAXIGP1AWVALID	      (0),
    .SAXIGP1BREADY	      (0),
    .SAXIGP1RREADY	      (0),
    .SAXIGP1WDATA	      (0),
    .SAXIGP1WID	              (0),
    .SAXIGP1WLAST	      (0),
    .SAXIGP1WSTRB	      (0),
    .SAXIGP1WVALID	      (0),
    .MIO                      (ps_mio),
    .PSCLK                    (ps_clk),
    .PSPORB                   (ps_porb),
    .PSSRSTB                  (ps_srstb),
    .FCLKCLK                  (FCLK),
    .FCLKRESETN               (FCLK_RESET0_N),
    .IRQF2P                   (IRQF2P),
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
    .MAXIGP0WVALID            (MAXIGP0WVALID),
    .SAXIHP0ACLK              (SAXIHP0ACLK),
    .SAXIHP0ARADDR            (SAXIHP0ARADDR),
    .SAXIHP0ARBURST           (SAXIHP0ARBURST),
    .SAXIHP0ARCACHE           (SAXIHP0ARCACHE),
    .SAXIHP0ARESETN           (SAXIHP0ARESETN),
    .SAXIHP0ARID              ({0, SAXIHP0ARID}),
    .SAXIHP0ARLEN             (SAXIHP0ARLEN),
    .SAXIHP0ARLOCK            (SAXIHP0ARLOCK),
    .SAXIHP0ARPROT            (SAXIHP0ARPROT),
    .SAXIHP0ARQOS             (SAXIHP0ARQOS),
    .SAXIHP0ARREADY           (SAXIHP0ARREADY),
    .SAXIHP0ARSIZE            (SAXIHP0ARSIZE),
    .SAXIHP0ARVALID           (SAXIHP0ARVALID),
    .SAXIHP0AWADDR            (SAXIHP0AWADDR),
    .SAXIHP0AWBURST           (SAXIHP0AWBURST),
    .SAXIHP0AWCACHE           (SAXIHP0AWCACHE),
    .SAXIHP0AWID              ({0, SAXIHP0AWID}),
    .SAXIHP0AWLEN             (SAXIHP0AWLEN),
    .SAXIHP0AWLOCK            (SAXIHP0AWLOCK),
    .SAXIHP0AWPROT            (SAXIHP0AWPROT),
    .SAXIHP0AWQOS             (SAXIHP0AWQOS),
    .SAXIHP0AWREADY           (SAXIHP0AWREADY),
    .SAXIHP0AWSIZE            (SAXIHP0AWSIZE),
    .SAXIHP0AWVALID           (SAXIHP0AWVALID),
    .SAXIHP0BID               (SAXIHP0BID),
    .SAXIHP0BREADY            (SAXIHP0BREADY),
    .SAXIHP0BRESP             (SAXIHP0BRESP),
    .SAXIHP0BVALID            (SAXIHP0BVALID),
    .SAXIHP0RACOUNT           (SAXIHP0RACOUNT),
    .SAXIHP0RCOUNT            (SAXIHP0RCOUNT),
    .SAXIHP0RDATA             (SAXIHP0RDATA),
    .SAXIHP0RDISSUECAP1EN     (SAXIHP0RDISSUECAP1EN),
    .SAXIHP0RID               (SAXIHP0RID),
    .SAXIHP0RLAST             (SAXIHP0RLAST),
    .SAXIHP0RREADY            (SAXIHP0RREADY),
    .SAXIHP0RRESP             (SAXIHP0RRESP),
    .SAXIHP0RVALID            (SAXIHP0RVALID),
    .SAXIHP0WACOUNT           (SAXIHP0WACOUNT),
    .SAXIHP0WCOUNT            (SAXIHP0WCOUNT),
    .SAXIHP0WDATA             (SAXIHP0WDATA),
    .SAXIHP0WID               ({0, SAXIHP0WID}),
    .SAXIHP0WLAST             (SAXIHP0WLAST),
    .SAXIHP0WREADY            (SAXIHP0WREADY),
    .SAXIHP0WRISSUECAP1EN     (SAXIHP0WRISSUECAP1EN),
    .SAXIHP0WSTRB             (SAXIHP0WSTRB),
    .SAXIHP0WVALID            (SAXIHP0WVALID),
    .SAXIHP1ACLK		    (0),
    .SAXIHP1ARADDR		    (0),
    .SAXIHP1ARBURST		    (0),
    .SAXIHP1ARCACHE		    (0),
    .SAXIHP1ARID		    (0),
    .SAXIHP1ARLEN		    (0),
    .SAXIHP1ARLOCK		    (0),
    .SAXIHP1ARPROT		    (0),
    .SAXIHP1ARQOS		    (0),
    .SAXIHP1ARSIZE		    (0),
    .SAXIHP1ARVALID		    (0),
    .SAXIHP1AWADDR		    (0),
    .SAXIHP1AWBURST		    (0),
    .SAXIHP1AWCACHE		    (0),
    .SAXIHP1AWID		    (0),
    .SAXIHP1AWLEN		    (0),
    .SAXIHP1AWLOCK		    (0),
    .SAXIHP1AWPROT		    (0),
    .SAXIHP1AWQOS		    (0),
    .SAXIHP1AWSIZE		    (0),
    .SAXIHP1AWVALID		    (0),
    .SAXIHP1BREADY		    (0),
    .SAXIHP1RDISSUECAP1EN	    (0),
    .SAXIHP1RREADY		    (0),
    .SAXIHP1WDATA		    (0),
    .SAXIHP1WID		            (0),
    .SAXIHP1WLAST		    (0),
    .SAXIHP1WRISSUECAP1EN	    (0),
    .SAXIHP1WSTRB		    (0),
    .SAXIHP1WVALID		    (0),
    .SAXIHP2ACLK		    (0),
    .SAXIHP2ARADDR		    (0),
    .SAXIHP2ARBURST		    (0),
    .SAXIHP2ARCACHE		    (0),
    .SAXIHP2ARID		    (0),
    .SAXIHP2ARLEN		    (0),
    .SAXIHP2ARLOCK		    (0),
    .SAXIHP2ARPROT		    (0),
    .SAXIHP2ARQOS		    (0),
    .SAXIHP2ARSIZE		    (0),
    .SAXIHP2ARVALID		    (0),
    .SAXIHP2AWADDR		    (0),
    .SAXIHP2AWBURST		    (0),
    .SAXIHP2AWCACHE		    (0),
    .SAXIHP2AWID		    (0),
    .SAXIHP2AWLEN		    (0),
    .SAXIHP2AWLOCK		    (0),
    .SAXIHP2AWPROT		    (0),
    .SAXIHP2AWQOS		    (0),
    .SAXIHP2AWSIZE		    (0),
    .SAXIHP2AWVALID		    (0),
    .SAXIHP2BREADY		    (0),
    .SAXIHP2RDISSUECAP1EN	    (0),
    .SAXIHP2RREADY		    (0),
    .SAXIHP2WDATA		    (0),
    .SAXIHP2WID		            (0),
    .SAXIHP2WLAST		    (0),
    .SAXIHP2WRISSUECAP1EN	    (0),
    .SAXIHP2WSTRB		    (0),
    .SAXIHP2WVALID		    (0),
    .SAXIHP3ACLK		    (0),
    .SAXIHP3ARADDR		    (0),
    .SAXIHP3ARBURST		    (0),
    .SAXIHP3ARCACHE		    (0),
    .SAXIHP3ARID		    (0),
    .SAXIHP3ARLEN		    (0),
    .SAXIHP3ARLOCK		    (0),
    .SAXIHP3ARPROT		    (0),
    .SAXIHP3ARQOS		    (0),
    .SAXIHP3ARSIZE		    (0),
    .SAXIHP3ARVALID		    (0),
    .SAXIHP3AWADDR		    (0),
    .SAXIHP3AWBURST		    (0),
    .SAXIHP3AWCACHE		    (0),
    .SAXIHP3AWID		    (0),
    .SAXIHP3AWLEN		    (0),
    .SAXIHP3AWLOCK		    (0),
    .SAXIHP3AWPROT		    (0),
    .SAXIHP3AWQOS		    (0),
    .SAXIHP3AWSIZE		    (0),
    .SAXIHP3AWVALID		    (0),
    .SAXIHP3BREADY		    (0),
    .SAXIHP3RDISSUECAP1EN	    (0),
    .SAXIHP3RREADY		    (0),
    .SAXIHP3WDATA		    (0),
    .SAXIHP3WID		            (0),
    .SAXIHP3WLAST		    (0),
    .SAXIHP3WRISSUECAP1EN      	    (0),
    .SAXIHP3WSTRB		    (0),
    .SAXIHP3WVALID		    (0)
    );

endmodule
