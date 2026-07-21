interface AXI4Lite;
  logic AWREADY;
  logic WREADY;
  logic BVALID;
  logic ARREADY;
  logic RVALID;
  logic RDATA;
  logic AWVALID;
  logic AWADDR;
  logic WVALID;
  logic WDATA;
  logic BREADY;
  logic ARVALID;
  logic ARADDR;
  logic RREADY;
  logic BID;
  logic RID;
  logic BRESP;
  logic RRESP;
  logic AWID;
  logic ARID;
  logic WSTRB;
  logic AWPROT;
  logic ARPROT;

  modport manager(
    input AWREADY, WREADY, BVALID, ARREADY, RVALID, RDATA, BID, RID, BRESP, RRESP,
    output AWVALID, AWADDR, WVALID, WDATA, BREADY, ARVALID, ARADDR, RREADY, AWID, ARID, WSTRB, AWPROT, ARPROT
  );

  modport subordinate(
    output AWREADY, WREADY, BVALID, ARREADY, RVALID, RDATA, BID, RID, BRESP, RRESP,
    input AWVALID, AWADDR, WVALID, WDATA, BREADY, ARVALID, ARADDR, RREADY, AWID, ARID, WSTRB, AWPROT, ARPROT
  );

  modport unspecified(
    input AWREADY, WREADY, BVALID, ARREADY, RVALID, RDATA, BID, RID, BRESP, RRESP,
    output AWVALID, AWADDR, WVALID, WDATA, BREADY, ARVALID, ARADDR, RREADY, AWID, ARID, WSTRB, AWPROT, ARPROT
  );

endinterface

