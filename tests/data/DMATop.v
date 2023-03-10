module DMATop( // @[:@1324.2]
  input         clock, // @[:@1325.4]
  input         reset, // @[:@1326.4]
  input  [31:0] io_control_aw_awaddr, // @[:@1327.4]
  input  [2:0]  io_control_aw_awprot, // @[:@1327.4]
  input         io_control_aw_awvalid, // @[:@1327.4]
  output        io_control_aw_awready, // @[:@1327.4]
  input  [31:0] io_control_w_wdata, // @[:@1327.4]
  input  [3:0]  io_control_w_wstrb, // @[:@1327.4]
  input         io_control_w_wvalid, // @[:@1327.4]
  output        io_control_w_wready, // @[:@1327.4]
  output [1:0]  io_control_b_bresp, // @[:@1327.4]
  output        io_control_b_bvalid, // @[:@1327.4]
  input         io_control_b_bready, // @[:@1327.4]
  input  [31:0] io_control_ar_araddr, // @[:@1327.4]
  input  [2:0]  io_control_ar_arprot, // @[:@1327.4]
  input         io_control_ar_arvalid, // @[:@1327.4]
  output        io_control_ar_arready, // @[:@1327.4]
  output [31:0] io_control_r_rdata, // @[:@1327.4]
  output [1:0]  io_control_r_rresp, // @[:@1327.4]
  output        io_control_r_rvalid, // @[:@1327.4]
  input         io_control_r_rready, // @[:@1327.4]
  output [3:0]  io_read_aw_awid, // @[:@1327.4]
  output [31:0] io_read_aw_awaddr, // @[:@1327.4]
  output [7:0]  io_read_aw_awlen, // @[:@1327.4]
  output [2:0]  io_read_aw_awsize, // @[:@1327.4]
  output [1:0]  io_read_aw_awburst, // @[:@1327.4]
  output        io_read_aw_awlock, // @[:@1327.4]
  output [3:0]  io_read_aw_awcache, // @[:@1327.4]
  output [2:0]  io_read_aw_awprot, // @[:@1327.4]
  output [3:0]  io_read_aw_awqos, // @[:@1327.4]
  output        io_read_aw_awvalid, // @[:@1327.4]
  input         io_read_aw_awready, // @[:@1327.4]
  output [63:0] io_read_w_wdata, // @[:@1327.4]
  output [7:0]  io_read_w_wstrb, // @[:@1327.4]
  output        io_read_w_wlast, // @[:@1327.4]
  output        io_read_w_wvalid, // @[:@1327.4]
  input         io_read_w_wready, // @[:@1327.4]
  input  [3:0]  io_read_b_bid, // @[:@1327.4]
  input  [1:0]  io_read_b_bresp, // @[:@1327.4]
  input         io_read_b_bvalid, // @[:@1327.4]
  output        io_read_b_bready, // @[:@1327.4]
  output [3:0]  io_read_ar_arid, // @[:@1327.4]
  output [31:0] io_read_ar_araddr, // @[:@1327.4]
  output [7:0]  io_read_ar_arlen, // @[:@1327.4]
  output [2:0]  io_read_ar_arsize, // @[:@1327.4]
  output [1:0]  io_read_ar_arburst, // @[:@1327.4]
  output        io_read_ar_arlock, // @[:@1327.4]
  output [3:0]  io_read_ar_arcache, // @[:@1327.4]
  output [2:0]  io_read_ar_arprot, // @[:@1327.4]
  output [3:0]  io_read_ar_arqos, // @[:@1327.4]
  output        io_read_ar_arvalid, // @[:@1327.4]
  input         io_read_ar_arready, // @[:@1327.4]
  input  [3:0]  io_read_r_rid, // @[:@1327.4]
  input  [63:0] io_read_r_rdata, // @[:@1327.4]
  input  [1:0]  io_read_r_rresp, // @[:@1327.4]
  input         io_read_r_rlast, // @[:@1327.4]
  input         io_read_r_rvalid, // @[:@1327.4]
  output        io_read_r_rready, // @[:@1327.4]
  output [63:0] io_write_tdata, // @[:@1327.4]
  output        io_write_tvalid, // @[:@1327.4]
  input         io_write_tready, // @[:@1327.4]
  output        io_write_tuser, // @[:@1327.4]
  output        io_write_tlast, // @[:@1327.4]
  output        io_irq_readerDone, // @[:@1327.4]
  output        io_irq_writerDone, // @[:@1327.4]
  input         io_sync_readerSync, // @[:@1327.4]
  input         io_sync_writerSync // @[:@1327.4]
);
  wire  csrFrontend_clock; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_reset; // @[DMATop.scala 42:27:@1329.4]
  wire [31:0] csrFrontend_io_ctl_aw_awaddr; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_aw_awvalid; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_aw_awready; // @[DMATop.scala 42:27:@1329.4]
  wire [31:0] csrFrontend_io_ctl_w_wdata; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_w_wvalid; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_w_wready; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_b_bvalid; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_b_bready; // @[DMATop.scala 42:27:@1329.4]
  wire [31:0] csrFrontend_io_ctl_ar_araddr; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_ar_arvalid; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_ar_arready; // @[DMATop.scala 42:27:@1329.4]
  wire [31:0] csrFrontend_io_ctl_r_rdata; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_r_rvalid; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_ctl_r_rready; // @[DMATop.scala 42:27:@1329.4]
  wire [3:0] csrFrontend_io_bus_addr; // @[DMATop.scala 42:27:@1329.4]
  wire [31:0] csrFrontend_io_bus_dataOut; // @[DMATop.scala 42:27:@1329.4]
  wire [31:0] csrFrontend_io_bus_dataIn; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_bus_write; // @[DMATop.scala 42:27:@1329.4]
  wire  csrFrontend_io_bus_read; // @[DMATop.scala 42:27:@1329.4]
  wire  readerFrontend_clock; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_reset; // @[DMATop.scala 44:30:@1332.4]
  wire [31:0] readerFrontend_io_bus_ar_araddr; // @[DMATop.scala 44:30:@1332.4]
  wire [7:0] readerFrontend_io_bus_ar_arlen; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_bus_ar_arvalid; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_bus_ar_arready; // @[DMATop.scala 44:30:@1332.4]
  wire [63:0] readerFrontend_io_bus_r_rdata; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_bus_r_rlast; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_bus_r_rvalid; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_bus_r_rready; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_dataOut_ready; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_dataOut_valid; // @[DMATop.scala 44:30:@1332.4]
  wire [63:0] readerFrontend_io_dataOut_bits; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_xfer_done; // @[DMATop.scala 44:30:@1332.4]
  wire [31:0] readerFrontend_io_xfer_address; // @[DMATop.scala 44:30:@1332.4]
  wire [31:0] readerFrontend_io_xfer_length; // @[DMATop.scala 44:30:@1332.4]
  wire  readerFrontend_io_xfer_valid; // @[DMATop.scala 44:30:@1332.4]
  wire  writerFrontend_clock; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_reset; // @[DMATop.scala 46:30:@1335.4]
  wire [63:0] writerFrontend_io_bus_tdata; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_bus_tvalid; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_bus_tready; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_bus_tlast; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_dataIn_ready; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_dataIn_valid; // @[DMATop.scala 46:30:@1335.4]
  wire [63:0] writerFrontend_io_dataIn_bits; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_xfer_done; // @[DMATop.scala 46:30:@1335.4]
  wire [31:0] writerFrontend_io_xfer_length; // @[DMATop.scala 46:30:@1335.4]
  wire  writerFrontend_io_xfer_valid; // @[DMATop.scala 46:30:@1335.4]
  wire [31:0] csr_io_csr_0_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_0_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_0_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_1_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_2_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_2_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_2_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_3_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_3_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_3_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_4_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_4_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_4_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_5_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_5_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_5_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_6_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_6_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_6_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_7_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_7_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_7_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_8_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_8_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_8_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_9_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_9_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_9_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_10_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_10_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_10_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_11_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_11_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_11_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_12_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_12_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_12_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_13_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_13_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_13_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_14_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_14_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_14_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_15_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_csr_15_dataWrite; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_csr_15_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire [3:0] csr_io_bus_addr; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_bus_dataOut; // @[DMATop.scala 48:19:@1338.4]
  wire [31:0] csr_io_bus_dataIn; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_bus_write; // @[DMATop.scala 48:19:@1338.4]
  wire  csr_io_bus_read; // @[DMATop.scala 48:19:@1338.4]
  wire  ctl_clock; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_reset; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_0_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_0_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_0_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_1_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_2_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_2_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_2_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_3_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_3_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_3_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_4_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_4_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_4_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_5_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_5_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_5_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_6_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_6_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_6_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_7_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_7_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_7_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_8_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_8_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_8_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_9_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_9_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_9_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_10_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_10_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_10_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_11_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_11_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_11_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_12_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_12_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_12_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_13_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_13_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_13_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_14_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_14_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_14_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_15_dataOut; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_csr_15_dataWrite; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_csr_15_dataIn; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_irq_readerDone; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_irq_writerDone; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_sync_readerSync; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_sync_writerSync; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_xferRead_done; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_xferRead_address; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_xferRead_length; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_xferRead_valid; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_xferWrite_done; // @[DMATop.scala 50:19:@1341.4]
  wire [31:0] ctl_io_xferWrite_length; // @[DMATop.scala 50:19:@1341.4]
  wire  ctl_io_xferWrite_valid; // @[DMATop.scala 50:19:@1341.4]
  wire  queue_clock; // @[Decoupled.scala 294:21:@1344.4]
  wire  queue_reset; // @[Decoupled.scala 294:21:@1344.4]
  wire  queue_io_enq_ready; // @[Decoupled.scala 294:21:@1344.4]
  wire  queue_io_enq_valid; // @[Decoupled.scala 294:21:@1344.4]
  wire [63:0] queue_io_enq_bits; // @[Decoupled.scala 294:21:@1344.4]
  wire  queue_io_deq_ready; // @[Decoupled.scala 294:21:@1344.4]
  wire  queue_io_deq_valid; // @[Decoupled.scala 294:21:@1344.4]
  wire [63:0] queue_io_deq_bits; // @[Decoupled.scala 294:21:@1344.4]
  AXI4LiteCSR csrFrontend ( // @[DMATop.scala 42:27:@1329.4]
    .clock(csrFrontend_clock),
    .reset(csrFrontend_reset),
    .io_ctl_aw_awaddr(csrFrontend_io_ctl_aw_awaddr),
    .io_ctl_aw_awvalid(csrFrontend_io_ctl_aw_awvalid),
    .io_ctl_aw_awready(csrFrontend_io_ctl_aw_awready),
    .io_ctl_w_wdata(csrFrontend_io_ctl_w_wdata),
    .io_ctl_w_wvalid(csrFrontend_io_ctl_w_wvalid),
    .io_ctl_w_wready(csrFrontend_io_ctl_w_wready),
    .io_ctl_b_bvalid(csrFrontend_io_ctl_b_bvalid),
    .io_ctl_b_bready(csrFrontend_io_ctl_b_bready),
    .io_ctl_ar_araddr(csrFrontend_io_ctl_ar_araddr),
    .io_ctl_ar_arvalid(csrFrontend_io_ctl_ar_arvalid),
    .io_ctl_ar_arready(csrFrontend_io_ctl_ar_arready),
    .io_ctl_r_rdata(csrFrontend_io_ctl_r_rdata),
    .io_ctl_r_rvalid(csrFrontend_io_ctl_r_rvalid),
    .io_ctl_r_rready(csrFrontend_io_ctl_r_rready),
    .io_bus_addr(csrFrontend_io_bus_addr),
    .io_bus_dataOut(csrFrontend_io_bus_dataOut),
    .io_bus_dataIn(csrFrontend_io_bus_dataIn),
    .io_bus_write(csrFrontend_io_bus_write),
    .io_bus_read(csrFrontend_io_bus_read)
  );
  AXI4Reader readerFrontend ( // @[DMATop.scala 44:30:@1332.4]
    .clock(readerFrontend_clock),
    .reset(readerFrontend_reset),
    .io_bus_ar_araddr(readerFrontend_io_bus_ar_araddr),
    .io_bus_ar_arlen(readerFrontend_io_bus_ar_arlen),
    .io_bus_ar_arvalid(readerFrontend_io_bus_ar_arvalid),
    .io_bus_ar_arready(readerFrontend_io_bus_ar_arready),
    .io_bus_r_rdata(readerFrontend_io_bus_r_rdata),
    .io_bus_r_rlast(readerFrontend_io_bus_r_rlast),
    .io_bus_r_rvalid(readerFrontend_io_bus_r_rvalid),
    .io_bus_r_rready(readerFrontend_io_bus_r_rready),
    .io_dataOut_ready(readerFrontend_io_dataOut_ready),
    .io_dataOut_valid(readerFrontend_io_dataOut_valid),
    .io_dataOut_bits(readerFrontend_io_dataOut_bits),
    .io_xfer_done(readerFrontend_io_xfer_done),
    .io_xfer_address(readerFrontend_io_xfer_address),
    .io_xfer_length(readerFrontend_io_xfer_length),
    .io_xfer_valid(readerFrontend_io_xfer_valid)
  );
  AXIStreamMaster writerFrontend ( // @[DMATop.scala 46:30:@1335.4]
    .clock(writerFrontend_clock),
    .reset(writerFrontend_reset),
    .io_bus_tdata(writerFrontend_io_bus_tdata),
    .io_bus_tvalid(writerFrontend_io_bus_tvalid),
    .io_bus_tready(writerFrontend_io_bus_tready),
    .io_bus_tlast(writerFrontend_io_bus_tlast),
    .io_dataIn_ready(writerFrontend_io_dataIn_ready),
    .io_dataIn_valid(writerFrontend_io_dataIn_valid),
    .io_dataIn_bits(writerFrontend_io_dataIn_bits),
    .io_xfer_done(writerFrontend_io_xfer_done),
    .io_xfer_length(writerFrontend_io_xfer_length),
    .io_xfer_valid(writerFrontend_io_xfer_valid)
  );
  CSR csr ( // @[DMATop.scala 48:19:@1338.4]
    .io_csr_0_dataOut(csr_io_csr_0_dataOut),
    .io_csr_0_dataWrite(csr_io_csr_0_dataWrite),
    .io_csr_0_dataIn(csr_io_csr_0_dataIn),
    .io_csr_1_dataIn(csr_io_csr_1_dataIn),
    .io_csr_2_dataOut(csr_io_csr_2_dataOut),
    .io_csr_2_dataWrite(csr_io_csr_2_dataWrite),
    .io_csr_2_dataIn(csr_io_csr_2_dataIn),
    .io_csr_3_dataOut(csr_io_csr_3_dataOut),
    .io_csr_3_dataWrite(csr_io_csr_3_dataWrite),
    .io_csr_3_dataIn(csr_io_csr_3_dataIn),
    .io_csr_4_dataOut(csr_io_csr_4_dataOut),
    .io_csr_4_dataWrite(csr_io_csr_4_dataWrite),
    .io_csr_4_dataIn(csr_io_csr_4_dataIn),
    .io_csr_5_dataOut(csr_io_csr_5_dataOut),
    .io_csr_5_dataWrite(csr_io_csr_5_dataWrite),
    .io_csr_5_dataIn(csr_io_csr_5_dataIn),
    .io_csr_6_dataOut(csr_io_csr_6_dataOut),
    .io_csr_6_dataWrite(csr_io_csr_6_dataWrite),
    .io_csr_6_dataIn(csr_io_csr_6_dataIn),
    .io_csr_7_dataOut(csr_io_csr_7_dataOut),
    .io_csr_7_dataWrite(csr_io_csr_7_dataWrite),
    .io_csr_7_dataIn(csr_io_csr_7_dataIn),
    .io_csr_8_dataOut(csr_io_csr_8_dataOut),
    .io_csr_8_dataWrite(csr_io_csr_8_dataWrite),
    .io_csr_8_dataIn(csr_io_csr_8_dataIn),
    .io_csr_9_dataOut(csr_io_csr_9_dataOut),
    .io_csr_9_dataWrite(csr_io_csr_9_dataWrite),
    .io_csr_9_dataIn(csr_io_csr_9_dataIn),
    .io_csr_10_dataOut(csr_io_csr_10_dataOut),
    .io_csr_10_dataWrite(csr_io_csr_10_dataWrite),
    .io_csr_10_dataIn(csr_io_csr_10_dataIn),
    .io_csr_11_dataOut(csr_io_csr_11_dataOut),
    .io_csr_11_dataWrite(csr_io_csr_11_dataWrite),
    .io_csr_11_dataIn(csr_io_csr_11_dataIn),
    .io_csr_12_dataOut(csr_io_csr_12_dataOut),
    .io_csr_12_dataWrite(csr_io_csr_12_dataWrite),
    .io_csr_12_dataIn(csr_io_csr_12_dataIn),
    .io_csr_13_dataOut(csr_io_csr_13_dataOut),
    .io_csr_13_dataWrite(csr_io_csr_13_dataWrite),
    .io_csr_13_dataIn(csr_io_csr_13_dataIn),
    .io_csr_14_dataOut(csr_io_csr_14_dataOut),
    .io_csr_14_dataWrite(csr_io_csr_14_dataWrite),
    .io_csr_14_dataIn(csr_io_csr_14_dataIn),
    .io_csr_15_dataOut(csr_io_csr_15_dataOut),
    .io_csr_15_dataWrite(csr_io_csr_15_dataWrite),
    .io_csr_15_dataIn(csr_io_csr_15_dataIn),
    .io_bus_addr(csr_io_bus_addr),
    .io_bus_dataOut(csr_io_bus_dataOut),
    .io_bus_dataIn(csr_io_bus_dataIn),
    .io_bus_write(csr_io_bus_write),
    .io_bus_read(csr_io_bus_read)
  );
  WorkerCSRWrapper ctl ( // @[DMATop.scala 50:19:@1341.4]
    .clock(ctl_clock),
    .reset(ctl_reset),
    .io_csr_0_dataOut(ctl_io_csr_0_dataOut),
    .io_csr_0_dataWrite(ctl_io_csr_0_dataWrite),
    .io_csr_0_dataIn(ctl_io_csr_0_dataIn),
    .io_csr_1_dataIn(ctl_io_csr_1_dataIn),
    .io_csr_2_dataOut(ctl_io_csr_2_dataOut),
    .io_csr_2_dataWrite(ctl_io_csr_2_dataWrite),
    .io_csr_2_dataIn(ctl_io_csr_2_dataIn),
    .io_csr_3_dataOut(ctl_io_csr_3_dataOut),
    .io_csr_3_dataWrite(ctl_io_csr_3_dataWrite),
    .io_csr_3_dataIn(ctl_io_csr_3_dataIn),
    .io_csr_4_dataOut(ctl_io_csr_4_dataOut),
    .io_csr_4_dataWrite(ctl_io_csr_4_dataWrite),
    .io_csr_4_dataIn(ctl_io_csr_4_dataIn),
    .io_csr_5_dataOut(ctl_io_csr_5_dataOut),
    .io_csr_5_dataWrite(ctl_io_csr_5_dataWrite),
    .io_csr_5_dataIn(ctl_io_csr_5_dataIn),
    .io_csr_6_dataOut(ctl_io_csr_6_dataOut),
    .io_csr_6_dataWrite(ctl_io_csr_6_dataWrite),
    .io_csr_6_dataIn(ctl_io_csr_6_dataIn),
    .io_csr_7_dataOut(ctl_io_csr_7_dataOut),
    .io_csr_7_dataWrite(ctl_io_csr_7_dataWrite),
    .io_csr_7_dataIn(ctl_io_csr_7_dataIn),
    .io_csr_8_dataOut(ctl_io_csr_8_dataOut),
    .io_csr_8_dataWrite(ctl_io_csr_8_dataWrite),
    .io_csr_8_dataIn(ctl_io_csr_8_dataIn),
    .io_csr_9_dataOut(ctl_io_csr_9_dataOut),
    .io_csr_9_dataWrite(ctl_io_csr_9_dataWrite),
    .io_csr_9_dataIn(ctl_io_csr_9_dataIn),
    .io_csr_10_dataOut(ctl_io_csr_10_dataOut),
    .io_csr_10_dataWrite(ctl_io_csr_10_dataWrite),
    .io_csr_10_dataIn(ctl_io_csr_10_dataIn),
    .io_csr_11_dataOut(ctl_io_csr_11_dataOut),
    .io_csr_11_dataWrite(ctl_io_csr_11_dataWrite),
    .io_csr_11_dataIn(ctl_io_csr_11_dataIn),
    .io_csr_12_dataOut(ctl_io_csr_12_dataOut),
    .io_csr_12_dataWrite(ctl_io_csr_12_dataWrite),
    .io_csr_12_dataIn(ctl_io_csr_12_dataIn),
    .io_csr_13_dataOut(ctl_io_csr_13_dataOut),
    .io_csr_13_dataWrite(ctl_io_csr_13_dataWrite),
    .io_csr_13_dataIn(ctl_io_csr_13_dataIn),
    .io_csr_14_dataOut(ctl_io_csr_14_dataOut),
    .io_csr_14_dataWrite(ctl_io_csr_14_dataWrite),
    .io_csr_14_dataIn(ctl_io_csr_14_dataIn),
    .io_csr_15_dataOut(ctl_io_csr_15_dataOut),
    .io_csr_15_dataWrite(ctl_io_csr_15_dataWrite),
    .io_csr_15_dataIn(ctl_io_csr_15_dataIn),
    .io_irq_readerDone(ctl_io_irq_readerDone),
    .io_irq_writerDone(ctl_io_irq_writerDone),
    .io_sync_readerSync(ctl_io_sync_readerSync),
    .io_sync_writerSync(ctl_io_sync_writerSync),
    .io_xferRead_done(ctl_io_xferRead_done),
    .io_xferRead_address(ctl_io_xferRead_address),
    .io_xferRead_length(ctl_io_xferRead_length),
    .io_xferRead_valid(ctl_io_xferRead_valid),
    .io_xferWrite_done(ctl_io_xferWrite_done),
    .io_xferWrite_length(ctl_io_xferWrite_length),
    .io_xferWrite_valid(ctl_io_xferWrite_valid)
  );
  Queue queue ( // @[Decoupled.scala 294:21:@1344.4]
    .clock(queue_clock),
    .reset(queue_reset),
    .io_enq_ready(queue_io_enq_ready),
    .io_enq_valid(queue_io_enq_valid),
    .io_enq_bits(queue_io_enq_bits),
    .io_deq_ready(queue_io_deq_ready),
    .io_deq_valid(queue_io_deq_valid),
    .io_deq_bits(queue_io_deq_bits)
  );
  assign io_control_aw_awready = csrFrontend_io_ctl_aw_awready; // @[DMATop.scala 56:22:@1368.4]
  assign io_control_w_wready = csrFrontend_io_ctl_w_wready; // @[DMATop.scala 56:22:@1364.4]
  assign io_control_b_bresp = 2'h0; // @[DMATop.scala 56:22:@1363.4]
  assign io_control_b_bvalid = csrFrontend_io_ctl_b_bvalid; // @[DMATop.scala 56:22:@1362.4]
  assign io_control_ar_arready = csrFrontend_io_ctl_ar_arready; // @[DMATop.scala 56:22:@1357.4]
  assign io_control_r_rdata = csrFrontend_io_ctl_r_rdata; // @[DMATop.scala 56:22:@1356.4]
  assign io_control_r_rresp = 2'h0; // @[DMATop.scala 56:22:@1355.4]
  assign io_control_r_rvalid = csrFrontend_io_ctl_r_rvalid; // @[DMATop.scala 56:22:@1354.4]
  assign io_read_aw_awid = 4'h0; // @[DMATop.scala 62:11:@1485.4]
  assign io_read_aw_awaddr = 32'h0; // @[DMATop.scala 62:11:@1484.4]
  assign io_read_aw_awlen = 8'h0; // @[DMATop.scala 62:11:@1483.4]
  assign io_read_aw_awsize = 3'h0; // @[DMATop.scala 62:11:@1482.4]
  assign io_read_aw_awburst = 2'h0; // @[DMATop.scala 62:11:@1481.4]
  assign io_read_aw_awlock = 1'h0; // @[DMATop.scala 62:11:@1480.4]
  assign io_read_aw_awcache = 4'h0; // @[DMATop.scala 62:11:@1479.4]
  assign io_read_aw_awprot = 3'h0; // @[DMATop.scala 62:11:@1478.4]
  assign io_read_aw_awqos = 4'h0; // @[DMATop.scala 62:11:@1477.4]
  assign io_read_aw_awvalid = 1'h0; // @[DMATop.scala 62:11:@1476.4]
  assign io_read_w_wdata = 64'h0; // @[DMATop.scala 62:11:@1474.4]
  assign io_read_w_wstrb = 8'h0; // @[DMATop.scala 62:11:@1473.4]
  assign io_read_w_wlast = 1'h0; // @[DMATop.scala 62:11:@1472.4]
  assign io_read_w_wvalid = 1'h0; // @[DMATop.scala 62:11:@1471.4]
  assign io_read_b_bready = 1'h0; // @[DMATop.scala 62:11:@1466.4]
  assign io_read_ar_arid = 4'h0; // @[DMATop.scala 62:11:@1465.4]
  assign io_read_ar_araddr = readerFrontend_io_bus_ar_araddr; // @[DMATop.scala 62:11:@1464.4]
  assign io_read_ar_arlen = readerFrontend_io_bus_ar_arlen; // @[DMATop.scala 62:11:@1463.4]
  assign io_read_ar_arsize = 3'h3; // @[DMATop.scala 62:11:@1462.4]
  assign io_read_ar_arburst = 2'h1; // @[DMATop.scala 62:11:@1461.4]
  assign io_read_ar_arlock = 1'h0; // @[DMATop.scala 62:11:@1460.4]
  assign io_read_ar_arcache = 4'h2; // @[DMATop.scala 62:11:@1459.4]
  assign io_read_ar_arprot = 3'h0; // @[DMATop.scala 62:11:@1458.4]
  assign io_read_ar_arqos = 4'h0; // @[DMATop.scala 62:11:@1457.4]
  assign io_read_ar_arvalid = readerFrontend_io_bus_ar_arvalid; // @[DMATop.scala 62:11:@1456.4]
  assign io_read_r_rready = readerFrontend_io_bus_r_rready; // @[DMATop.scala 62:11:@1449.4]
  assign io_write_tdata = writerFrontend_io_bus_tdata; // @[DMATop.scala 63:12:@1490.4]
  assign io_write_tvalid = writerFrontend_io_bus_tvalid; // @[DMATop.scala 63:12:@1489.4]
  assign io_write_tuser = 1'h0; // @[DMATop.scala 63:12:@1487.4]
  assign io_write_tlast = writerFrontend_io_bus_tlast; // @[DMATop.scala 63:12:@1486.4]
  assign io_irq_readerDone = ctl_io_irq_readerDone; // @[DMATop.scala 65:10:@1492.4]
  assign io_irq_writerDone = ctl_io_irq_writerDone; // @[DMATop.scala 65:10:@1491.4]
  assign csrFrontend_clock = clock; // @[:@1330.4]
  assign csrFrontend_reset = reset; // @[:@1331.4]
  assign csrFrontend_io_ctl_aw_awaddr = io_control_aw_awaddr; // @[DMATop.scala 56:22:@1371.4]
  assign csrFrontend_io_ctl_aw_awvalid = io_control_aw_awvalid; // @[DMATop.scala 56:22:@1369.4]
  assign csrFrontend_io_ctl_w_wdata = io_control_w_wdata; // @[DMATop.scala 56:22:@1367.4]
  assign csrFrontend_io_ctl_w_wvalid = io_control_w_wvalid; // @[DMATop.scala 56:22:@1365.4]
  assign csrFrontend_io_ctl_b_bready = io_control_b_bready; // @[DMATop.scala 56:22:@1361.4]
  assign csrFrontend_io_ctl_ar_araddr = io_control_ar_araddr; // @[DMATop.scala 56:22:@1360.4]
  assign csrFrontend_io_ctl_ar_arvalid = io_control_ar_arvalid; // @[DMATop.scala 56:22:@1358.4]
  assign csrFrontend_io_ctl_r_rready = io_control_r_rready; // @[DMATop.scala 56:22:@1353.4]
  assign csrFrontend_io_bus_dataIn = csr_io_bus_dataIn; // @[DMATop.scala 57:14:@1374.4]
  assign readerFrontend_clock = clock; // @[:@1333.4]
  assign readerFrontend_reset = reset; // @[:@1334.4]
  assign readerFrontend_io_bus_ar_arready = io_read_ar_arready; // @[DMATop.scala 62:11:@1455.4]
  assign readerFrontend_io_bus_r_rdata = io_read_r_rdata; // @[DMATop.scala 62:11:@1453.4]
  assign readerFrontend_io_bus_r_rlast = io_read_r_rlast; // @[DMATop.scala 62:11:@1451.4]
  assign readerFrontend_io_bus_r_rvalid = io_read_r_rvalid; // @[DMATop.scala 62:11:@1450.4]
  assign readerFrontend_io_dataOut_ready = queue_io_enq_ready; // @[Decoupled.scala 297:17:@1349.4]
  assign readerFrontend_io_xfer_address = ctl_io_xferRead_address; // @[DMATop.scala 59:26:@1443.4]
  assign readerFrontend_io_xfer_length = ctl_io_xferRead_length; // @[DMATop.scala 59:26:@1442.4]
  assign readerFrontend_io_xfer_valid = ctl_io_xferRead_valid; // @[DMATop.scala 59:26:@1441.4]
  assign writerFrontend_clock = clock; // @[:@1336.4]
  assign writerFrontend_reset = reset; // @[:@1337.4]
  assign writerFrontend_io_bus_tready = io_write_tready; // @[DMATop.scala 63:12:@1488.4]
  assign writerFrontend_io_dataIn_valid = queue_io_deq_valid; // @[DMATop.scala 54:9:@1351.4]
  assign writerFrontend_io_dataIn_bits = queue_io_deq_bits; // @[DMATop.scala 54:9:@1350.4]
  assign writerFrontend_io_xfer_length = ctl_io_xferWrite_length; // @[DMATop.scala 60:26:@1446.4]
  assign writerFrontend_io_xfer_valid = ctl_io_xferWrite_valid; // @[DMATop.scala 60:26:@1445.4]
  assign csr_io_csr_0_dataIn = ctl_io_csr_0_dataIn; // @[DMATop.scala 58:14:@1377.4]
  assign csr_io_csr_1_dataIn = ctl_io_csr_1_dataIn; // @[DMATop.scala 58:14:@1381.4]
  assign csr_io_csr_2_dataIn = ctl_io_csr_2_dataIn; // @[DMATop.scala 58:14:@1385.4]
  assign csr_io_csr_3_dataIn = ctl_io_csr_3_dataIn; // @[DMATop.scala 58:14:@1389.4]
  assign csr_io_csr_4_dataIn = ctl_io_csr_4_dataIn; // @[DMATop.scala 58:14:@1393.4]
  assign csr_io_csr_5_dataIn = ctl_io_csr_5_dataIn; // @[DMATop.scala 58:14:@1397.4]
  assign csr_io_csr_6_dataIn = ctl_io_csr_6_dataIn; // @[DMATop.scala 58:14:@1401.4]
  assign csr_io_csr_7_dataIn = ctl_io_csr_7_dataIn; // @[DMATop.scala 58:14:@1405.4]
  assign csr_io_csr_8_dataIn = ctl_io_csr_8_dataIn; // @[DMATop.scala 58:14:@1409.4]
  assign csr_io_csr_9_dataIn = ctl_io_csr_9_dataIn; // @[DMATop.scala 58:14:@1413.4]
  assign csr_io_csr_10_dataIn = ctl_io_csr_10_dataIn; // @[DMATop.scala 58:14:@1417.4]
  assign csr_io_csr_11_dataIn = ctl_io_csr_11_dataIn; // @[DMATop.scala 58:14:@1421.4]
  assign csr_io_csr_12_dataIn = ctl_io_csr_12_dataIn; // @[DMATop.scala 58:14:@1425.4]
  assign csr_io_csr_13_dataIn = ctl_io_csr_13_dataIn; // @[DMATop.scala 58:14:@1429.4]
  assign csr_io_csr_14_dataIn = ctl_io_csr_14_dataIn; // @[DMATop.scala 58:14:@1433.4]
  assign csr_io_csr_15_dataIn = ctl_io_csr_15_dataIn; // @[DMATop.scala 58:14:@1437.4]
  assign csr_io_bus_addr = csrFrontend_io_bus_addr; // @[DMATop.scala 57:14:@1376.4]
  assign csr_io_bus_dataOut = csrFrontend_io_bus_dataOut; // @[DMATop.scala 57:14:@1375.4]
  assign csr_io_bus_write = csrFrontend_io_bus_write; // @[DMATop.scala 57:14:@1373.4]
  assign csr_io_bus_read = csrFrontend_io_bus_read; // @[DMATop.scala 57:14:@1372.4]
  assign ctl_clock = clock; // @[:@1342.4]
  assign ctl_reset = reset; // @[:@1343.4]
  assign ctl_io_csr_0_dataOut = csr_io_csr_0_dataOut; // @[DMATop.scala 58:14:@1379.4]
  assign ctl_io_csr_0_dataWrite = csr_io_csr_0_dataWrite; // @[DMATop.scala 58:14:@1378.4]
  assign ctl_io_csr_2_dataOut = csr_io_csr_2_dataOut; // @[DMATop.scala 58:14:@1387.4]
  assign ctl_io_csr_2_dataWrite = csr_io_csr_2_dataWrite; // @[DMATop.scala 58:14:@1386.4]
  assign ctl_io_csr_3_dataOut = csr_io_csr_3_dataOut; // @[DMATop.scala 58:14:@1391.4]
  assign ctl_io_csr_3_dataWrite = csr_io_csr_3_dataWrite; // @[DMATop.scala 58:14:@1390.4]
  assign ctl_io_csr_4_dataOut = csr_io_csr_4_dataOut; // @[DMATop.scala 58:14:@1395.4]
  assign ctl_io_csr_4_dataWrite = csr_io_csr_4_dataWrite; // @[DMATop.scala 58:14:@1394.4]
  assign ctl_io_csr_5_dataOut = csr_io_csr_5_dataOut; // @[DMATop.scala 58:14:@1399.4]
  assign ctl_io_csr_5_dataWrite = csr_io_csr_5_dataWrite; // @[DMATop.scala 58:14:@1398.4]
  assign ctl_io_csr_6_dataOut = csr_io_csr_6_dataOut; // @[DMATop.scala 58:14:@1403.4]
  assign ctl_io_csr_6_dataWrite = csr_io_csr_6_dataWrite; // @[DMATop.scala 58:14:@1402.4]
  assign ctl_io_csr_7_dataOut = csr_io_csr_7_dataOut; // @[DMATop.scala 58:14:@1407.4]
  assign ctl_io_csr_7_dataWrite = csr_io_csr_7_dataWrite; // @[DMATop.scala 58:14:@1406.4]
  assign ctl_io_csr_8_dataOut = csr_io_csr_8_dataOut; // @[DMATop.scala 58:14:@1411.4]
  assign ctl_io_csr_8_dataWrite = csr_io_csr_8_dataWrite; // @[DMATop.scala 58:14:@1410.4]
  assign ctl_io_csr_9_dataOut = csr_io_csr_9_dataOut; // @[DMATop.scala 58:14:@1415.4]
  assign ctl_io_csr_9_dataWrite = csr_io_csr_9_dataWrite; // @[DMATop.scala 58:14:@1414.4]
  assign ctl_io_csr_10_dataOut = csr_io_csr_10_dataOut; // @[DMATop.scala 58:14:@1419.4]
  assign ctl_io_csr_10_dataWrite = csr_io_csr_10_dataWrite; // @[DMATop.scala 58:14:@1418.4]
  assign ctl_io_csr_11_dataOut = csr_io_csr_11_dataOut; // @[DMATop.scala 58:14:@1423.4]
  assign ctl_io_csr_11_dataWrite = csr_io_csr_11_dataWrite; // @[DMATop.scala 58:14:@1422.4]
  assign ctl_io_csr_12_dataOut = csr_io_csr_12_dataOut; // @[DMATop.scala 58:14:@1427.4]
  assign ctl_io_csr_12_dataWrite = csr_io_csr_12_dataWrite; // @[DMATop.scala 58:14:@1426.4]
  assign ctl_io_csr_13_dataOut = csr_io_csr_13_dataOut; // @[DMATop.scala 58:14:@1431.4]
  assign ctl_io_csr_13_dataWrite = csr_io_csr_13_dataWrite; // @[DMATop.scala 58:14:@1430.4]
  assign ctl_io_csr_14_dataOut = csr_io_csr_14_dataOut; // @[DMATop.scala 58:14:@1435.4]
  assign ctl_io_csr_14_dataWrite = csr_io_csr_14_dataWrite; // @[DMATop.scala 58:14:@1434.4]
  assign ctl_io_csr_15_dataOut = csr_io_csr_15_dataOut; // @[DMATop.scala 58:14:@1439.4]
  assign ctl_io_csr_15_dataWrite = csr_io_csr_15_dataWrite; // @[DMATop.scala 58:14:@1438.4]
  assign ctl_io_sync_readerSync = io_sync_readerSync; // @[DMATop.scala 66:11:@1494.4]
  assign ctl_io_sync_writerSync = io_sync_writerSync; // @[DMATop.scala 66:11:@1493.4]
  assign ctl_io_xferRead_done = readerFrontend_io_xfer_done; // @[DMATop.scala 59:26:@1444.4]
  assign ctl_io_xferWrite_done = writerFrontend_io_xfer_done; // @[DMATop.scala 60:26:@1448.4]
  assign queue_clock = clock; // @[:@1345.4]
  assign queue_reset = reset; // @[:@1346.4]
  assign queue_io_enq_valid = readerFrontend_io_dataOut_valid; // @[Decoupled.scala 295:22:@1347.4]
  assign queue_io_enq_bits = readerFrontend_io_dataOut_bits; // @[Decoupled.scala 296:21:@1348.4]
  assign queue_io_deq_ready = writerFrontend_io_dataIn_ready; // @[DMATop.scala 54:9:@1352.4]
endmodule
