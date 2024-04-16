(* generator = "Amaranth" *)
module wb_interconnect (rst, wb_ram_instr_mem_bus_dat_w, wb_ram_instr_mem_bus_bte, wb_ram_instr_mem_bus_sel, wb_ram_instr_mem_bus_cyc, wb_ram_instr_mem_bus_cti, wb_ram_instr_mem_bus_adr, wb_ram_instr_mem_bus_stb, wb_ram_instr_mem_bus_we, wb_ram_instr_mem_bus_dat_r, wb_ram_instr_mem_bus_ack, wb_ram_data_mem_bus_dat_w, wb_ram_data_mem_bus_bte, wb_ram_data_mem_bus_sel, wb_ram_data_mem_bus_cyc, wb_ram_data_mem_bus_cti, wb_ram_data_mem_bus_adr, wb_ram_data_mem_bus_stb, wb_ram_data_mem_bus_we, wb_ram_data_mem_bus_dat_r, wb_ram_data_mem_bus_ack
, wb_uart_csr_wishbone_dat_w, wb_uart_csr_wishbone_bte, wb_uart_csr_wishbone_sel, wb_uart_csr_wishbone_cyc, wb_uart_csr_wishbone_cti, wb_uart_csr_wishbone_adr, wb_uart_csr_wishbone_stb, wb_uart_csr_wishbone_we, wb_uart_csr_wishbone_dat_r, wb_uart_csr_wishbone_ack, vexriscv_iBusWishbone_dat_r, vexriscv_iBusWishbone_ack, vexriscv_iBusWishbone_err, vexriscv_iBusWishbone_dat_w, vexriscv_iBusWishbone_bte, vexriscv_iBusWishbone_sel, vexriscv_iBusWishbone_cyc, vexriscv_iBusWishbone_cti, vexriscv_iBusWishbone_adr, vexriscv_iBusWishbone_stb, vexriscv_iBusWishbone_we
, vexriscv_dBusWishbone_dat_r, vexriscv_dBusWishbone_ack, vexriscv_dBusWishbone_err, vexriscv_dBusWishbone_dat_w, vexriscv_dBusWishbone_bte, vexriscv_dBusWishbone_sel, vexriscv_dBusWishbone_cyc, vexriscv_dBusWishbone_cti, vexriscv_dBusWishbone_adr, vexriscv_dBusWishbone_stb, vexriscv_dBusWishbone_we, clk);
  wire \U$$0_interconnect0_clk ;
  wire \U$$0_interconnect0_rst ;
  wire \U$$0_vexriscv_dBusWishbone__ack ;
  wire [29:0] \U$$0_vexriscv_dBusWishbone__adr ;
  wire [1:0] \U$$0_vexriscv_dBusWishbone__bte ;
  wire [2:0] \U$$0_vexriscv_dBusWishbone__cti ;
  wire \U$$0_vexriscv_dBusWishbone__cyc ;
  wire [31:0] \U$$0_vexriscv_dBusWishbone__dat_r ;
  wire [31:0] \U$$0_vexriscv_dBusWishbone__dat_w ;
  wire \U$$0_vexriscv_dBusWishbone__err ;
  wire [3:0] \U$$0_vexriscv_dBusWishbone__sel ;
  wire \U$$0_vexriscv_dBusWishbone__stb ;
  wire \U$$0_vexriscv_dBusWishbone__we ;
  wire \U$$0_vexriscv_iBusWishbone__ack ;
  wire [29:0] \U$$0_vexriscv_iBusWishbone__adr ;
  wire [1:0] \U$$0_vexriscv_iBusWishbone__bte ;
  wire [2:0] \U$$0_vexriscv_iBusWishbone__cti ;
  wire \U$$0_vexriscv_iBusWishbone__cyc ;
  wire [31:0] \U$$0_vexriscv_iBusWishbone__dat_r ;
  wire [31:0] \U$$0_vexriscv_iBusWishbone__dat_w ;
  wire \U$$0_vexriscv_iBusWishbone__err ;
  wire [3:0] \U$$0_vexriscv_iBusWishbone__sel ;
  wire \U$$0_vexriscv_iBusWishbone__stb ;
  wire \U$$0_vexriscv_iBusWishbone__we ;
  wire \U$$0_wb_ram_data_mem_bus__ack ;
  wire [11:0] \U$$0_wb_ram_data_mem_bus__adr ;
  wire [1:0] \U$$0_wb_ram_data_mem_bus__bte ;
  wire [2:0] \U$$0_wb_ram_data_mem_bus__cti ;
  wire \U$$0_wb_ram_data_mem_bus__cyc ;
  wire [31:0] \U$$0_wb_ram_data_mem_bus__dat_r ;
  wire [31:0] \U$$0_wb_ram_data_mem_bus__dat_w ;
  wire \U$$0_wb_ram_data_mem_bus__err ;
  wire [3:0] \U$$0_wb_ram_data_mem_bus__sel ;
  wire \U$$0_wb_ram_data_mem_bus__stb ;
  wire \U$$0_wb_ram_data_mem_bus__we ;
  wire \U$$0_wb_ram_instr_mem_bus__ack ;
  wire [15:0] \U$$0_wb_ram_instr_mem_bus__adr ;
  wire [1:0] \U$$0_wb_ram_instr_mem_bus__bte ;
  wire [2:0] \U$$0_wb_ram_instr_mem_bus__cti ;
  wire \U$$0_wb_ram_instr_mem_bus__cyc ;
  wire [31:0] \U$$0_wb_ram_instr_mem_bus__dat_r ;
  wire [31:0] \U$$0_wb_ram_instr_mem_bus__dat_w ;
  wire \U$$0_wb_ram_instr_mem_bus__err ;
  wire [3:0] \U$$0_wb_ram_instr_mem_bus__sel ;
  wire \U$$0_wb_ram_instr_mem_bus__stb ;
  wire \U$$0_wb_ram_instr_mem_bus__we ;
  wire \U$$0_wb_uart_csr_wishbone__ack ;
  wire [11:0] \U$$0_wb_uart_csr_wishbone__adr ;
  wire [1:0] \U$$0_wb_uart_csr_wishbone__bte ;
  wire [2:0] \U$$0_wb_uart_csr_wishbone__cti ;
  wire \U$$0_wb_uart_csr_wishbone__cyc ;
  wire [31:0] \U$$0_wb_uart_csr_wishbone__dat_r ;
  wire [31:0] \U$$0_wb_uart_csr_wishbone__dat_w ;
  wire \U$$0_wb_uart_csr_wishbone__err ;
  wire [3:0] \U$$0_wb_uart_csr_wishbone__sel ;
  wire \U$$0_wb_uart_csr_wishbone__stb ;
  wire \U$$0_wb_uart_csr_wishbone__we ;
  input clk;
  wire clk;
  input rst;
  wire rst;
  output vexriscv_dBusWishbone_ack;
  wire vexriscv_dBusWishbone_ack;
  input [29:0] vexriscv_dBusWishbone_adr;
  wire [29:0] vexriscv_dBusWishbone_adr;
  input [1:0] vexriscv_dBusWishbone_bte;
  wire [1:0] vexriscv_dBusWishbone_bte;
  input [2:0] vexriscv_dBusWishbone_cti;
  wire [2:0] vexriscv_dBusWishbone_cti;
  input vexriscv_dBusWishbone_cyc;
  wire vexriscv_dBusWishbone_cyc;
  output [31:0] vexriscv_dBusWishbone_dat_r;
  wire [31:0] vexriscv_dBusWishbone_dat_r;
  input [31:0] vexriscv_dBusWishbone_dat_w;
  wire [31:0] vexriscv_dBusWishbone_dat_w;
  output vexriscv_dBusWishbone_err;
  wire vexriscv_dBusWishbone_err;
  input [3:0] vexriscv_dBusWishbone_sel;
  wire [3:0] vexriscv_dBusWishbone_sel;
  input vexriscv_dBusWishbone_stb;
  wire vexriscv_dBusWishbone_stb;
  input vexriscv_dBusWishbone_we;
  wire vexriscv_dBusWishbone_we;
  output vexriscv_iBusWishbone_ack;
  wire vexriscv_iBusWishbone_ack;
  input [29:0] vexriscv_iBusWishbone_adr;
  wire [29:0] vexriscv_iBusWishbone_adr;
  input [1:0] vexriscv_iBusWishbone_bte;
  wire [1:0] vexriscv_iBusWishbone_bte;
  input [2:0] vexriscv_iBusWishbone_cti;
  wire [2:0] vexriscv_iBusWishbone_cti;
  input vexriscv_iBusWishbone_cyc;
  wire vexriscv_iBusWishbone_cyc;
  output [31:0] vexriscv_iBusWishbone_dat_r;
  wire [31:0] vexriscv_iBusWishbone_dat_r;
  input [31:0] vexriscv_iBusWishbone_dat_w;
  wire [31:0] vexriscv_iBusWishbone_dat_w;
  output vexriscv_iBusWishbone_err;
  wire vexriscv_iBusWishbone_err;
  input [3:0] vexriscv_iBusWishbone_sel;
  wire [3:0] vexriscv_iBusWishbone_sel;
  input vexriscv_iBusWishbone_stb;
  wire vexriscv_iBusWishbone_stb;
  input vexriscv_iBusWishbone_we;
  wire vexriscv_iBusWishbone_we;
  input wb_ram_data_mem_bus_ack;
  wire wb_ram_data_mem_bus_ack;
  output [11:0] wb_ram_data_mem_bus_adr;
  wire [11:0] wb_ram_data_mem_bus_adr;
  output [1:0] wb_ram_data_mem_bus_bte;
  wire [1:0] wb_ram_data_mem_bus_bte;
  output [2:0] wb_ram_data_mem_bus_cti;
  wire [2:0] wb_ram_data_mem_bus_cti;
  output wb_ram_data_mem_bus_cyc;
  wire wb_ram_data_mem_bus_cyc;
  input [31:0] wb_ram_data_mem_bus_dat_r;
  wire [31:0] wb_ram_data_mem_bus_dat_r;
  output [31:0] wb_ram_data_mem_bus_dat_w;
  wire [31:0] wb_ram_data_mem_bus_dat_w;
  wire wb_ram_data_mem_bus_err;
  output [3:0] wb_ram_data_mem_bus_sel;
  wire [3:0] wb_ram_data_mem_bus_sel;
  output wb_ram_data_mem_bus_stb;
  wire wb_ram_data_mem_bus_stb;
  output wb_ram_data_mem_bus_we;
  wire wb_ram_data_mem_bus_we;
  input wb_ram_instr_mem_bus_ack;
  wire wb_ram_instr_mem_bus_ack;
  output [15:0] wb_ram_instr_mem_bus_adr;
  wire [15:0] wb_ram_instr_mem_bus_adr;
  output [1:0] wb_ram_instr_mem_bus_bte;
  wire [1:0] wb_ram_instr_mem_bus_bte;
  output [2:0] wb_ram_instr_mem_bus_cti;
  wire [2:0] wb_ram_instr_mem_bus_cti;
  output wb_ram_instr_mem_bus_cyc;
  wire wb_ram_instr_mem_bus_cyc;
  input [31:0] wb_ram_instr_mem_bus_dat_r;
  wire [31:0] wb_ram_instr_mem_bus_dat_r;
  output [31:0] wb_ram_instr_mem_bus_dat_w;
  wire [31:0] wb_ram_instr_mem_bus_dat_w;
  wire wb_ram_instr_mem_bus_err;
  output [3:0] wb_ram_instr_mem_bus_sel;
  wire [3:0] wb_ram_instr_mem_bus_sel;
  output wb_ram_instr_mem_bus_stb;
  wire wb_ram_instr_mem_bus_stb;
  output wb_ram_instr_mem_bus_we;
  wire wb_ram_instr_mem_bus_we;
  input wb_uart_csr_wishbone_ack;
  wire wb_uart_csr_wishbone_ack;
  output [11:0] wb_uart_csr_wishbone_adr;
  wire [11:0] wb_uart_csr_wishbone_adr;
  output [1:0] wb_uart_csr_wishbone_bte;
  wire [1:0] wb_uart_csr_wishbone_bte;
  output [2:0] wb_uart_csr_wishbone_cti;
  wire [2:0] wb_uart_csr_wishbone_cti;
  output wb_uart_csr_wishbone_cyc;
  wire wb_uart_csr_wishbone_cyc;
  input [31:0] wb_uart_csr_wishbone_dat_r;
  wire [31:0] wb_uart_csr_wishbone_dat_r;
  output [31:0] wb_uart_csr_wishbone_dat_w;
  wire [31:0] wb_uart_csr_wishbone_dat_w;
  wire wb_uart_csr_wishbone_err;
  output [3:0] wb_uart_csr_wishbone_sel;
  wire [3:0] wb_uart_csr_wishbone_sel;
  output wb_uart_csr_wishbone_stb;
  wire wb_uart_csr_wishbone_stb;
  output wb_uart_csr_wishbone_we;
  wire wb_uart_csr_wishbone_we;
  \simple_soc.interconnect0.U$$0  \U$$0  (
    .interconnect0_clk(\U$$0_interconnect0_clk ),
    .interconnect0_rst(\U$$0_interconnect0_rst ),
    .vexriscv_dBusWishbone__ack(\U$$0_vexriscv_dBusWishbone__ack ),
    .vexriscv_dBusWishbone__adr(\U$$0_vexriscv_dBusWishbone__adr ),
    .vexriscv_dBusWishbone__bte(\U$$0_vexriscv_dBusWishbone__bte ),
    .vexriscv_dBusWishbone__cti(\U$$0_vexriscv_dBusWishbone__cti ),
    .vexriscv_dBusWishbone__cyc(\U$$0_vexriscv_dBusWishbone__cyc ),
    .vexriscv_dBusWishbone__dat_r(\U$$0_vexriscv_dBusWishbone__dat_r ),
    .vexriscv_dBusWishbone__dat_w(\U$$0_vexriscv_dBusWishbone__dat_w ),
    .vexriscv_dBusWishbone__err(\U$$0_vexriscv_dBusWishbone__err ),
    .vexriscv_dBusWishbone__sel(\U$$0_vexriscv_dBusWishbone__sel ),
    .vexriscv_dBusWishbone__stb(\U$$0_vexriscv_dBusWishbone__stb ),
    .vexriscv_dBusWishbone__we(\U$$0_vexriscv_dBusWishbone__we ),
    .vexriscv_iBusWishbone__ack(\U$$0_vexriscv_iBusWishbone__ack ),
    .vexriscv_iBusWishbone__adr(\U$$0_vexriscv_iBusWishbone__adr ),
    .vexriscv_iBusWishbone__bte(\U$$0_vexriscv_iBusWishbone__bte ),
    .vexriscv_iBusWishbone__cti(\U$$0_vexriscv_iBusWishbone__cti ),
    .vexriscv_iBusWishbone__cyc(\U$$0_vexriscv_iBusWishbone__cyc ),
    .vexriscv_iBusWishbone__dat_r(\U$$0_vexriscv_iBusWishbone__dat_r ),
    .vexriscv_iBusWishbone__dat_w(\U$$0_vexriscv_iBusWishbone__dat_w ),
    .vexriscv_iBusWishbone__err(\U$$0_vexriscv_iBusWishbone__err ),
    .vexriscv_iBusWishbone__sel(\U$$0_vexriscv_iBusWishbone__sel ),
    .vexriscv_iBusWishbone__stb(\U$$0_vexriscv_iBusWishbone__stb ),
    .vexriscv_iBusWishbone__we(\U$$0_vexriscv_iBusWishbone__we ),
    .wb_ram_data_mem_bus__ack(\U$$0_wb_ram_data_mem_bus__ack ),
    .wb_ram_data_mem_bus__adr(\U$$0_wb_ram_data_mem_bus__adr ),
    .wb_ram_data_mem_bus__bte(\U$$0_wb_ram_data_mem_bus__bte ),
    .wb_ram_data_mem_bus__cti(\U$$0_wb_ram_data_mem_bus__cti ),
    .wb_ram_data_mem_bus__cyc(\U$$0_wb_ram_data_mem_bus__cyc ),
    .wb_ram_data_mem_bus__dat_r(\U$$0_wb_ram_data_mem_bus__dat_r ),
    .wb_ram_data_mem_bus__dat_w(\U$$0_wb_ram_data_mem_bus__dat_w ),
    .wb_ram_data_mem_bus__err(1'h0),
    .wb_ram_data_mem_bus__sel(\U$$0_wb_ram_data_mem_bus__sel ),
    .wb_ram_data_mem_bus__stb(\U$$0_wb_ram_data_mem_bus__stb ),
    .wb_ram_data_mem_bus__we(\U$$0_wb_ram_data_mem_bus__we ),
    .wb_ram_instr_mem_bus__ack(\U$$0_wb_ram_instr_mem_bus__ack ),
    .wb_ram_instr_mem_bus__adr(\U$$0_wb_ram_instr_mem_bus__adr ),
    .wb_ram_instr_mem_bus__bte(\U$$0_wb_ram_instr_mem_bus__bte ),
    .wb_ram_instr_mem_bus__cti(\U$$0_wb_ram_instr_mem_bus__cti ),
    .wb_ram_instr_mem_bus__cyc(\U$$0_wb_ram_instr_mem_bus__cyc ),
    .wb_ram_instr_mem_bus__dat_r(\U$$0_wb_ram_instr_mem_bus__dat_r ),
    .wb_ram_instr_mem_bus__dat_w(\U$$0_wb_ram_instr_mem_bus__dat_w ),
    .wb_ram_instr_mem_bus__err(1'h0),
    .wb_ram_instr_mem_bus__sel(\U$$0_wb_ram_instr_mem_bus__sel ),
    .wb_ram_instr_mem_bus__stb(\U$$0_wb_ram_instr_mem_bus__stb ),
    .wb_ram_instr_mem_bus__we(\U$$0_wb_ram_instr_mem_bus__we ),
    .wb_uart_csr_wishbone__ack(\U$$0_wb_uart_csr_wishbone__ack ),
    .wb_uart_csr_wishbone__adr(\U$$0_wb_uart_csr_wishbone__adr ),
    .wb_uart_csr_wishbone__bte(\U$$0_wb_uart_csr_wishbone__bte ),
    .wb_uart_csr_wishbone__cti(\U$$0_wb_uart_csr_wishbone__cti ),
    .wb_uart_csr_wishbone__cyc(\U$$0_wb_uart_csr_wishbone__cyc ),
    .wb_uart_csr_wishbone__dat_r(\U$$0_wb_uart_csr_wishbone__dat_r ),
    .wb_uart_csr_wishbone__dat_w(\U$$0_wb_uart_csr_wishbone__dat_w ),
    .wb_uart_csr_wishbone__err(1'h0),
    .wb_uart_csr_wishbone__sel(\U$$0_wb_uart_csr_wishbone__sel ),
    .wb_uart_csr_wishbone__stb(\U$$0_wb_uart_csr_wishbone__stb ),
    .wb_uart_csr_wishbone__we(\U$$0_wb_uart_csr_wishbone__we )
  );
  assign wb_ram_instr_mem_bus_err = 1'h0;
  assign wb_ram_data_mem_bus_err = 1'h0;
  assign wb_uart_csr_wishbone_err = 1'h0;
  assign \U$$0_vexriscv_dBusWishbone__bte  = vexriscv_dBusWishbone_bte;
  assign \U$$0_vexriscv_dBusWishbone__cti  = vexriscv_dBusWishbone_cti;
  assign vexriscv_dBusWishbone_err = \U$$0_vexriscv_dBusWishbone__err ;
  assign vexriscv_dBusWishbone_ack = \U$$0_vexriscv_dBusWishbone__ack ;
  assign \U$$0_vexriscv_dBusWishbone__we  = vexriscv_dBusWishbone_we;
  assign \U$$0_vexriscv_dBusWishbone__stb  = vexriscv_dBusWishbone_stb;
  assign \U$$0_vexriscv_dBusWishbone__cyc  = vexriscv_dBusWishbone_cyc;
  assign \U$$0_vexriscv_dBusWishbone__sel  = vexriscv_dBusWishbone_sel;
  assign vexriscv_dBusWishbone_dat_r = \U$$0_vexriscv_dBusWishbone__dat_r ;
  assign \U$$0_vexriscv_dBusWishbone__dat_w  = vexriscv_dBusWishbone_dat_w;
  assign \U$$0_vexriscv_dBusWishbone__adr  = vexriscv_dBusWishbone_adr;
  assign \U$$0_vexriscv_iBusWishbone__bte  = vexriscv_iBusWishbone_bte;
  assign \U$$0_vexriscv_iBusWishbone__cti  = vexriscv_iBusWishbone_cti;
  assign vexriscv_iBusWishbone_err = \U$$0_vexriscv_iBusWishbone__err ;
  assign vexriscv_iBusWishbone_ack = \U$$0_vexriscv_iBusWishbone__ack ;
  assign \U$$0_vexriscv_iBusWishbone__we  = vexriscv_iBusWishbone_we;
  assign \U$$0_vexriscv_iBusWishbone__stb  = vexriscv_iBusWishbone_stb;
  assign \U$$0_vexriscv_iBusWishbone__cyc  = vexriscv_iBusWishbone_cyc;
  assign \U$$0_vexriscv_iBusWishbone__sel  = vexriscv_iBusWishbone_sel;
  assign vexriscv_iBusWishbone_dat_r = \U$$0_vexriscv_iBusWishbone__dat_r ;
  assign \U$$0_vexriscv_iBusWishbone__dat_w  = vexriscv_iBusWishbone_dat_w;
  assign \U$$0_vexriscv_iBusWishbone__adr  = vexriscv_iBusWishbone_adr;
  assign wb_uart_csr_wishbone_bte = \U$$0_wb_uart_csr_wishbone__bte ;
  assign wb_uart_csr_wishbone_cti = \U$$0_wb_uart_csr_wishbone__cti ;
  assign \U$$0_wb_uart_csr_wishbone__err  = 1'h0;
  assign \U$$0_wb_uart_csr_wishbone__ack  = wb_uart_csr_wishbone_ack;
  assign wb_uart_csr_wishbone_we = \U$$0_wb_uart_csr_wishbone__we ;
  assign wb_uart_csr_wishbone_stb = \U$$0_wb_uart_csr_wishbone__stb ;
  assign wb_uart_csr_wishbone_cyc = \U$$0_wb_uart_csr_wishbone__cyc ;
  assign wb_uart_csr_wishbone_sel = \U$$0_wb_uart_csr_wishbone__sel ;
  assign \U$$0_wb_uart_csr_wishbone__dat_r  = wb_uart_csr_wishbone_dat_r;
  assign wb_uart_csr_wishbone_dat_w = \U$$0_wb_uart_csr_wishbone__dat_w ;
  assign wb_uart_csr_wishbone_adr = \U$$0_wb_uart_csr_wishbone__adr ;
  assign wb_ram_data_mem_bus_bte = \U$$0_wb_ram_data_mem_bus__bte ;
  assign wb_ram_data_mem_bus_cti = \U$$0_wb_ram_data_mem_bus__cti ;
  assign \U$$0_wb_ram_data_mem_bus__err  = 1'h0;
  assign \U$$0_wb_ram_data_mem_bus__ack  = wb_ram_data_mem_bus_ack;
  assign wb_ram_data_mem_bus_we = \U$$0_wb_ram_data_mem_bus__we ;
  assign wb_ram_data_mem_bus_stb = \U$$0_wb_ram_data_mem_bus__stb ;
  assign wb_ram_data_mem_bus_cyc = \U$$0_wb_ram_data_mem_bus__cyc ;
  assign wb_ram_data_mem_bus_sel = \U$$0_wb_ram_data_mem_bus__sel ;
  assign \U$$0_wb_ram_data_mem_bus__dat_r  = wb_ram_data_mem_bus_dat_r;
  assign wb_ram_data_mem_bus_dat_w = \U$$0_wb_ram_data_mem_bus__dat_w ;
  assign wb_ram_data_mem_bus_adr = \U$$0_wb_ram_data_mem_bus__adr ;
  assign wb_ram_instr_mem_bus_bte = \U$$0_wb_ram_instr_mem_bus__bte ;
  assign wb_ram_instr_mem_bus_cti = \U$$0_wb_ram_instr_mem_bus__cti ;
  assign \U$$0_wb_ram_instr_mem_bus__err  = 1'h0;
  assign \U$$0_wb_ram_instr_mem_bus__ack  = wb_ram_instr_mem_bus_ack;
  assign wb_ram_instr_mem_bus_we = \U$$0_wb_ram_instr_mem_bus__we ;
  assign wb_ram_instr_mem_bus_stb = \U$$0_wb_ram_instr_mem_bus__stb ;
  assign wb_ram_instr_mem_bus_cyc = \U$$0_wb_ram_instr_mem_bus__cyc ;
  assign wb_ram_instr_mem_bus_sel = \U$$0_wb_ram_instr_mem_bus__sel ;
  assign \U$$0_wb_ram_instr_mem_bus__dat_r  = wb_ram_instr_mem_bus_dat_r;
  assign wb_ram_instr_mem_bus_dat_w = \U$$0_wb_ram_instr_mem_bus__dat_w ;
  assign wb_ram_instr_mem_bus_adr = \U$$0_wb_ram_instr_mem_bus__adr ;
  assign \U$$0_interconnect0_rst  = rst;
  assign \U$$0_interconnect0_clk  = clk;
endmodule
module \simple_soc.interconnect0.U$$0 (interconnect0_rst, wb_ram_instr_mem_bus__adr, wb_ram_instr_mem_bus__dat_w, wb_ram_instr_mem_bus__dat_r, wb_ram_instr_mem_bus__sel, wb_ram_instr_mem_bus__cyc, wb_ram_instr_mem_bus__stb, wb_ram_instr_mem_bus__we, wb_ram_instr_mem_bus__ack, wb_ram_instr_mem_bus__err, wb_ram_instr_mem_bus__cti, wb_ram_instr_mem_bus__bte, wb_ram_data_mem_bus__adr, wb_ram_data_mem_bus__dat_w, wb_ram_data_mem_bus__dat_r, wb_ram_data_mem_bus__sel, wb_ram_data_mem_bus__cyc, wb_ram_data_mem_bus__stb, wb_ram_data_mem_bus__we, wb_ram_data_mem_bus__ack, wb_ram_data_mem_bus__err
, wb_ram_data_mem_bus__cti, wb_ram_data_mem_bus__bte, wb_uart_csr_wishbone__adr, wb_uart_csr_wishbone__dat_w, wb_uart_csr_wishbone__dat_r, wb_uart_csr_wishbone__sel, wb_uart_csr_wishbone__cyc, wb_uart_csr_wishbone__stb, wb_uart_csr_wishbone__we, wb_uart_csr_wishbone__ack, wb_uart_csr_wishbone__err, wb_uart_csr_wishbone__cti, wb_uart_csr_wishbone__bte, vexriscv_iBusWishbone__adr, vexriscv_iBusWishbone__dat_w, vexriscv_iBusWishbone__dat_r, vexriscv_iBusWishbone__sel, vexriscv_iBusWishbone__cyc, vexriscv_iBusWishbone__stb, vexriscv_iBusWishbone__we, vexriscv_iBusWishbone__ack
, vexriscv_iBusWishbone__err, vexriscv_iBusWishbone__cti, vexriscv_iBusWishbone__bte, vexriscv_dBusWishbone__adr, vexriscv_dBusWishbone__dat_w, vexriscv_dBusWishbone__dat_r, vexriscv_dBusWishbone__sel, vexriscv_dBusWishbone__cyc, vexriscv_dBusWishbone__stb, vexriscv_dBusWishbone__we, vexriscv_dBusWishbone__ack, vexriscv_dBusWishbone__err, vexriscv_dBusWishbone__cti, vexriscv_dBusWishbone__bte, interconnect0_clk);
  wire arbiter_bus__ack;
  wire [29:0] arbiter_bus__adr;
  wire [1:0] arbiter_bus__bte;
  wire [2:0] arbiter_bus__cti;
  wire arbiter_bus__cyc;
  wire [31:0] arbiter_bus__dat_r;
  wire [31:0] arbiter_bus__dat_w;
  wire arbiter_bus__err;
  wire [3:0] arbiter_bus__sel;
  wire arbiter_bus__stb;
  wire arbiter_bus__we;
  wire decoder_bus__ack;
  wire [29:0] decoder_bus__adr;
  wire [1:0] decoder_bus__bte;
  wire [2:0] decoder_bus__cti;
  wire decoder_bus__cyc;
  wire [31:0] decoder_bus__dat_r;
  wire [31:0] decoder_bus__dat_w;
  wire decoder_bus__err;
  wire [3:0] decoder_bus__sel;
  wire decoder_bus__stb;
  wire decoder_bus__we;
  input interconnect0_clk;
  wire interconnect0_clk;
  input interconnect0_rst;
  wire interconnect0_rst;
  output vexriscv_dBusWishbone__ack;
  wire vexriscv_dBusWishbone__ack;
  input [29:0] vexriscv_dBusWishbone__adr;
  wire [29:0] vexriscv_dBusWishbone__adr;
  input [1:0] vexriscv_dBusWishbone__bte;
  wire [1:0] vexriscv_dBusWishbone__bte;
  input [2:0] vexriscv_dBusWishbone__cti;
  wire [2:0] vexriscv_dBusWishbone__cti;
  input vexriscv_dBusWishbone__cyc;
  wire vexriscv_dBusWishbone__cyc;
  output [31:0] vexriscv_dBusWishbone__dat_r;
  wire [31:0] vexriscv_dBusWishbone__dat_r;
  input [31:0] vexriscv_dBusWishbone__dat_w;
  wire [31:0] vexriscv_dBusWishbone__dat_w;
  output vexriscv_dBusWishbone__err;
  wire vexriscv_dBusWishbone__err;
  input [3:0] vexriscv_dBusWishbone__sel;
  wire [3:0] vexriscv_dBusWishbone__sel;
  input vexriscv_dBusWishbone__stb;
  wire vexriscv_dBusWishbone__stb;
  input vexriscv_dBusWishbone__we;
  wire vexriscv_dBusWishbone__we;
  output vexriscv_iBusWishbone__ack;
  wire vexriscv_iBusWishbone__ack;
  input [29:0] vexriscv_iBusWishbone__adr;
  wire [29:0] vexriscv_iBusWishbone__adr;
  input [1:0] vexriscv_iBusWishbone__bte;
  wire [1:0] vexriscv_iBusWishbone__bte;
  input [2:0] vexriscv_iBusWishbone__cti;
  wire [2:0] vexriscv_iBusWishbone__cti;
  input vexriscv_iBusWishbone__cyc;
  wire vexriscv_iBusWishbone__cyc;
  output [31:0] vexriscv_iBusWishbone__dat_r;
  wire [31:0] vexriscv_iBusWishbone__dat_r;
  input [31:0] vexriscv_iBusWishbone__dat_w;
  wire [31:0] vexriscv_iBusWishbone__dat_w;
  output vexriscv_iBusWishbone__err;
  wire vexriscv_iBusWishbone__err;
  input [3:0] vexriscv_iBusWishbone__sel;
  wire [3:0] vexriscv_iBusWishbone__sel;
  input vexriscv_iBusWishbone__stb;
  wire vexriscv_iBusWishbone__stb;
  input vexriscv_iBusWishbone__we;
  wire vexriscv_iBusWishbone__we;
  input wb_ram_data_mem_bus__ack;
  wire wb_ram_data_mem_bus__ack;
  output [11:0] wb_ram_data_mem_bus__adr;
  wire [11:0] wb_ram_data_mem_bus__adr;
  output [1:0] wb_ram_data_mem_bus__bte;
  wire [1:0] wb_ram_data_mem_bus__bte;
  output [2:0] wb_ram_data_mem_bus__cti;
  wire [2:0] wb_ram_data_mem_bus__cti;
  output wb_ram_data_mem_bus__cyc;
  wire wb_ram_data_mem_bus__cyc;
  input [31:0] wb_ram_data_mem_bus__dat_r;
  wire [31:0] wb_ram_data_mem_bus__dat_r;
  output [31:0] wb_ram_data_mem_bus__dat_w;
  wire [31:0] wb_ram_data_mem_bus__dat_w;
  input wb_ram_data_mem_bus__err;
  wire wb_ram_data_mem_bus__err;
  output [3:0] wb_ram_data_mem_bus__sel;
  wire [3:0] wb_ram_data_mem_bus__sel;
  output wb_ram_data_mem_bus__stb;
  wire wb_ram_data_mem_bus__stb;
  output wb_ram_data_mem_bus__we;
  wire wb_ram_data_mem_bus__we;
  input wb_ram_instr_mem_bus__ack;
  wire wb_ram_instr_mem_bus__ack;
  output [15:0] wb_ram_instr_mem_bus__adr;
  wire [15:0] wb_ram_instr_mem_bus__adr;
  output [1:0] wb_ram_instr_mem_bus__bte;
  wire [1:0] wb_ram_instr_mem_bus__bte;
  output [2:0] wb_ram_instr_mem_bus__cti;
  wire [2:0] wb_ram_instr_mem_bus__cti;
  output wb_ram_instr_mem_bus__cyc;
  wire wb_ram_instr_mem_bus__cyc;
  input [31:0] wb_ram_instr_mem_bus__dat_r;
  wire [31:0] wb_ram_instr_mem_bus__dat_r;
  output [31:0] wb_ram_instr_mem_bus__dat_w;
  wire [31:0] wb_ram_instr_mem_bus__dat_w;
  input wb_ram_instr_mem_bus__err;
  wire wb_ram_instr_mem_bus__err;
  output [3:0] wb_ram_instr_mem_bus__sel;
  wire [3:0] wb_ram_instr_mem_bus__sel;
  output wb_ram_instr_mem_bus__stb;
  wire wb_ram_instr_mem_bus__stb;
  output wb_ram_instr_mem_bus__we;
  wire wb_ram_instr_mem_bus__we;
  input wb_uart_csr_wishbone__ack;
  wire wb_uart_csr_wishbone__ack;
  output [11:0] wb_uart_csr_wishbone__adr;
  wire [11:0] wb_uart_csr_wishbone__adr;
  output [1:0] wb_uart_csr_wishbone__bte;
  wire [1:0] wb_uart_csr_wishbone__bte;
  output [2:0] wb_uart_csr_wishbone__cti;
  wire [2:0] wb_uart_csr_wishbone__cti;
  output wb_uart_csr_wishbone__cyc;
  wire wb_uart_csr_wishbone__cyc;
  input [31:0] wb_uart_csr_wishbone__dat_r;
  wire [31:0] wb_uart_csr_wishbone__dat_r;
  output [31:0] wb_uart_csr_wishbone__dat_w;
  wire [31:0] wb_uart_csr_wishbone__dat_w;
  input wb_uart_csr_wishbone__err;
  wire wb_uart_csr_wishbone__err;
  output [3:0] wb_uart_csr_wishbone__sel;
  wire [3:0] wb_uart_csr_wishbone__sel;
  output wb_uart_csr_wishbone__stb;
  wire wb_uart_csr_wishbone__stb;
  output wb_uart_csr_wishbone__we;
  wire wb_uart_csr_wishbone__we;
  \simple_soc.interconnect0.U$$0.arbiter  arbiter (
    .bus__ack(arbiter_bus__ack),
    .bus__adr(arbiter_bus__adr),
    .bus__bte(arbiter_bus__bte),
    .bus__cti(arbiter_bus__cti),
    .bus__cyc(arbiter_bus__cyc),
    .bus__dat_r(arbiter_bus__dat_r),
    .bus__dat_w(arbiter_bus__dat_w),
    .bus__err(arbiter_bus__err),
    .bus__sel(arbiter_bus__sel),
    .bus__stb(arbiter_bus__stb),
    .bus__we(arbiter_bus__we),
    .interconnect0_clk(interconnect0_clk),
    .interconnect0_rst(interconnect0_rst),
    .vexriscv_dBusWishbone__ack(vexriscv_dBusWishbone__ack),
    .vexriscv_dBusWishbone__adr(vexriscv_dBusWishbone__adr),
    .vexriscv_dBusWishbone__bte(vexriscv_dBusWishbone__bte),
    .vexriscv_dBusWishbone__cti(vexriscv_dBusWishbone__cti),
    .vexriscv_dBusWishbone__cyc(vexriscv_dBusWishbone__cyc),
    .vexriscv_dBusWishbone__dat_r(vexriscv_dBusWishbone__dat_r),
    .vexriscv_dBusWishbone__dat_w(vexriscv_dBusWishbone__dat_w),
    .vexriscv_dBusWishbone__err(vexriscv_dBusWishbone__err),
    .vexriscv_dBusWishbone__sel(vexriscv_dBusWishbone__sel),
    .vexriscv_dBusWishbone__stb(vexriscv_dBusWishbone__stb),
    .vexriscv_dBusWishbone__we(vexriscv_dBusWishbone__we),
    .vexriscv_iBusWishbone__ack(vexriscv_iBusWishbone__ack),
    .vexriscv_iBusWishbone__adr(vexriscv_iBusWishbone__adr),
    .vexriscv_iBusWishbone__bte(vexriscv_iBusWishbone__bte),
    .vexriscv_iBusWishbone__cti(vexriscv_iBusWishbone__cti),
    .vexriscv_iBusWishbone__cyc(vexriscv_iBusWishbone__cyc),
    .vexriscv_iBusWishbone__dat_r(vexriscv_iBusWishbone__dat_r),
    .vexriscv_iBusWishbone__dat_w(vexriscv_iBusWishbone__dat_w),
    .vexriscv_iBusWishbone__err(vexriscv_iBusWishbone__err),
    .vexriscv_iBusWishbone__sel(vexriscv_iBusWishbone__sel),
    .vexriscv_iBusWishbone__stb(vexriscv_iBusWishbone__stb),
    .vexriscv_iBusWishbone__we(vexriscv_iBusWishbone__we)
  );
  \simple_soc.interconnect0.U$$0.decoder  decoder (
    .bus__ack(decoder_bus__ack),
    .bus__adr(decoder_bus__adr),
    .bus__bte(decoder_bus__bte),
    .bus__cti(decoder_bus__cti),
    .bus__cyc(decoder_bus__cyc),
    .bus__dat_r(decoder_bus__dat_r),
    .bus__dat_w(decoder_bus__dat_w),
    .bus__err(decoder_bus__err),
    .bus__sel(decoder_bus__sel),
    .bus__stb(decoder_bus__stb),
    .bus__we(decoder_bus__we),
    .wb_ram_data_mem_bus__ack(wb_ram_data_mem_bus__ack),
    .wb_ram_data_mem_bus__adr(wb_ram_data_mem_bus__adr),
    .wb_ram_data_mem_bus__bte(wb_ram_data_mem_bus__bte),
    .wb_ram_data_mem_bus__cti(wb_ram_data_mem_bus__cti),
    .wb_ram_data_mem_bus__cyc(wb_ram_data_mem_bus__cyc),
    .wb_ram_data_mem_bus__dat_r(wb_ram_data_mem_bus__dat_r),
    .wb_ram_data_mem_bus__dat_w(wb_ram_data_mem_bus__dat_w),
    .wb_ram_data_mem_bus__err(wb_ram_data_mem_bus__err),
    .wb_ram_data_mem_bus__sel(wb_ram_data_mem_bus__sel),
    .wb_ram_data_mem_bus__stb(wb_ram_data_mem_bus__stb),
    .wb_ram_data_mem_bus__we(wb_ram_data_mem_bus__we),
    .wb_ram_instr_mem_bus__ack(wb_ram_instr_mem_bus__ack),
    .wb_ram_instr_mem_bus__adr(wb_ram_instr_mem_bus__adr),
    .wb_ram_instr_mem_bus__bte(wb_ram_instr_mem_bus__bte),
    .wb_ram_instr_mem_bus__cti(wb_ram_instr_mem_bus__cti),
    .wb_ram_instr_mem_bus__cyc(wb_ram_instr_mem_bus__cyc),
    .wb_ram_instr_mem_bus__dat_r(wb_ram_instr_mem_bus__dat_r),
    .wb_ram_instr_mem_bus__dat_w(wb_ram_instr_mem_bus__dat_w),
    .wb_ram_instr_mem_bus__err(wb_ram_instr_mem_bus__err),
    .wb_ram_instr_mem_bus__sel(wb_ram_instr_mem_bus__sel),
    .wb_ram_instr_mem_bus__stb(wb_ram_instr_mem_bus__stb),
    .wb_ram_instr_mem_bus__we(wb_ram_instr_mem_bus__we),
    .wb_uart_csr_wishbone__ack(wb_uart_csr_wishbone__ack),
    .wb_uart_csr_wishbone__adr(wb_uart_csr_wishbone__adr),
    .wb_uart_csr_wishbone__bte(wb_uart_csr_wishbone__bte),
    .wb_uart_csr_wishbone__cti(wb_uart_csr_wishbone__cti),
    .wb_uart_csr_wishbone__cyc(wb_uart_csr_wishbone__cyc),
    .wb_uart_csr_wishbone__dat_r(wb_uart_csr_wishbone__dat_r),
    .wb_uart_csr_wishbone__dat_w(wb_uart_csr_wishbone__dat_w),
    .wb_uart_csr_wishbone__err(wb_uart_csr_wishbone__err),
    .wb_uart_csr_wishbone__sel(wb_uart_csr_wishbone__sel),
    .wb_uart_csr_wishbone__stb(wb_uart_csr_wishbone__stb),
    .wb_uart_csr_wishbone__we(wb_uart_csr_wishbone__we)
  );
  assign decoder_bus__we = arbiter_bus__we;
  assign decoder_bus__stb = arbiter_bus__stb;
  assign decoder_bus__sel = arbiter_bus__sel;
  assign arbiter_bus__err = decoder_bus__err;
  assign decoder_bus__dat_w = arbiter_bus__dat_w;
  assign arbiter_bus__dat_r = decoder_bus__dat_r;
  assign decoder_bus__cyc = arbiter_bus__cyc;
  assign decoder_bus__cti = arbiter_bus__cti;
  assign decoder_bus__bte = arbiter_bus__bte;
  assign decoder_bus__adr = arbiter_bus__adr;
  assign arbiter_bus__ack = decoder_bus__ack;
endmodule
module \simple_soc.interconnect0.U$$0.arbiter (interconnect0_rst, vexriscv_iBusWishbone__adr, vexriscv_iBusWishbone__dat_w, vexriscv_iBusWishbone__dat_r, vexriscv_iBusWishbone__sel, vexriscv_iBusWishbone__cyc, vexriscv_iBusWishbone__stb, vexriscv_iBusWishbone__we, vexriscv_iBusWishbone__ack, vexriscv_iBusWishbone__err, vexriscv_iBusWishbone__cti, vexriscv_iBusWishbone__bte, vexriscv_dBusWishbone__adr, vexriscv_dBusWishbone__dat_w, vexriscv_dBusWishbone__dat_r, vexriscv_dBusWishbone__sel, vexriscv_dBusWishbone__cyc, vexriscv_dBusWishbone__stb, vexriscv_dBusWishbone__we, vexriscv_dBusWishbone__ack, vexriscv_dBusWishbone__err
, vexriscv_dBusWishbone__cti, vexriscv_dBusWishbone__bte, bus__ack, bus__adr, bus__bte, bus__cti, bus__cyc, bus__dat_r, bus__dat_w, bus__err, bus__sel, bus__stb, bus__we, interconnect0_clk);
  reg \$auto$verilog_backend.cc:2253:dump_module$1  = 0;
  wire \$1 ;
  input bus__ack;
  wire bus__ack;
  output [29:0] bus__adr;
  reg [29:0] bus__adr;
  output [1:0] bus__bte;
  reg [1:0] bus__bte;
  output [2:0] bus__cti;
  reg [2:0] bus__cti;
  output bus__cyc;
  reg bus__cyc;
  input [31:0] bus__dat_r;
  wire [31:0] bus__dat_r;
  output [31:0] bus__dat_w;
  reg [31:0] bus__dat_w;
  input bus__err;
  wire bus__err;
  output [3:0] bus__sel;
  reg [3:0] bus__sel;
  output bus__stb;
  reg bus__stb;
  output bus__we;
  reg bus__we;
  reg grant = 1'h0;
  reg \grant$next ;
  input interconnect0_clk;
  wire interconnect0_clk;
  input interconnect0_rst;
  wire interconnect0_rst;
  wire [1:0] requests;
  output vexriscv_dBusWishbone__ack;
  reg vexriscv_dBusWishbone__ack;
  input [29:0] vexriscv_dBusWishbone__adr;
  wire [29:0] vexriscv_dBusWishbone__adr;
  input [1:0] vexriscv_dBusWishbone__bte;
  wire [1:0] vexriscv_dBusWishbone__bte;
  input [2:0] vexriscv_dBusWishbone__cti;
  wire [2:0] vexriscv_dBusWishbone__cti;
  input vexriscv_dBusWishbone__cyc;
  wire vexriscv_dBusWishbone__cyc;
  output [31:0] vexriscv_dBusWishbone__dat_r;
  wire [31:0] vexriscv_dBusWishbone__dat_r;
  input [31:0] vexriscv_dBusWishbone__dat_w;
  wire [31:0] vexriscv_dBusWishbone__dat_w;
  output vexriscv_dBusWishbone__err;
  reg vexriscv_dBusWishbone__err;
  input [3:0] vexriscv_dBusWishbone__sel;
  wire [3:0] vexriscv_dBusWishbone__sel;
  input vexriscv_dBusWishbone__stb;
  wire vexriscv_dBusWishbone__stb;
  input vexriscv_dBusWishbone__we;
  wire vexriscv_dBusWishbone__we;
  output vexriscv_iBusWishbone__ack;
  reg vexriscv_iBusWishbone__ack;
  input [29:0] vexriscv_iBusWishbone__adr;
  wire [29:0] vexriscv_iBusWishbone__adr;
  input [1:0] vexriscv_iBusWishbone__bte;
  wire [1:0] vexriscv_iBusWishbone__bte;
  input [2:0] vexriscv_iBusWishbone__cti;
  wire [2:0] vexriscv_iBusWishbone__cti;
  input vexriscv_iBusWishbone__cyc;
  wire vexriscv_iBusWishbone__cyc;
  output [31:0] vexriscv_iBusWishbone__dat_r;
  wire [31:0] vexriscv_iBusWishbone__dat_r;
  input [31:0] vexriscv_iBusWishbone__dat_w;
  wire [31:0] vexriscv_iBusWishbone__dat_w;
  output vexriscv_iBusWishbone__err;
  reg vexriscv_iBusWishbone__err;
  input [3:0] vexriscv_iBusWishbone__sel;
  wire [3:0] vexriscv_iBusWishbone__sel;
  input vexriscv_iBusWishbone__stb;
  wire vexriscv_iBusWishbone__stb;
  input vexriscv_iBusWishbone__we;
  wire vexriscv_iBusWishbone__we;
  assign \$1  = ~bus__cyc;
  always @(posedge interconnect0_clk)
    grant <= \grant$next ;
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    \grant$next  = grant;
    if (\$1 )
      casez (grant)
        1'h0:
            if (requests[1])
              \grant$next  = 1'h1;
        1'h1:
            if (requests[0])
              \grant$next  = 1'h0;
      endcase
    if (interconnect0_rst)
      \grant$next  = 1'h0;
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__cti = vexriscv_iBusWishbone__cti;
      1'h1:
          bus__cti = vexriscv_dBusWishbone__cti;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__bte = vexriscv_iBusWishbone__bte;
      1'h1:
          bus__bte = vexriscv_dBusWishbone__bte;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    vexriscv_iBusWishbone__ack = 1'h0;
    casez (grant)
      1'h0:
          vexriscv_iBusWishbone__ack = bus__ack;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    vexriscv_iBusWishbone__err = 1'h0;
    casez (grant)
      1'h0:
          vexriscv_iBusWishbone__err = bus__err;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    vexriscv_dBusWishbone__ack = 1'h0;
    casez (grant)
      1'h0:
          /* empty */;
      1'h1:
          vexriscv_dBusWishbone__ack = bus__ack;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    vexriscv_dBusWishbone__err = 1'h0;
    casez (grant)
      1'h0:
          /* empty */;
      1'h1:
          vexriscv_dBusWishbone__err = bus__err;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__adr = vexriscv_iBusWishbone__adr;
      1'h1:
          bus__adr = vexriscv_dBusWishbone__adr;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__dat_w = vexriscv_iBusWishbone__dat_w;
      1'h1:
          bus__dat_w = vexriscv_dBusWishbone__dat_w;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__sel = vexriscv_iBusWishbone__sel;
      1'h1:
          bus__sel = vexriscv_dBusWishbone__sel;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__we = vexriscv_iBusWishbone__we;
      1'h1:
          bus__we = vexriscv_dBusWishbone__we;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__stb = vexriscv_iBusWishbone__stb;
      1'h1:
          bus__stb = vexriscv_dBusWishbone__stb;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$1 ) begin end
    casez (grant)
      1'h0:
          bus__cyc = vexriscv_iBusWishbone__cyc;
      1'h1:
          bus__cyc = vexriscv_dBusWishbone__cyc;
    endcase
  end
  assign vexriscv_dBusWishbone__dat_r = bus__dat_r;
  assign vexriscv_iBusWishbone__dat_r = bus__dat_r;
  assign requests = { vexriscv_dBusWishbone__cyc, vexriscv_iBusWishbone__cyc };
endmodule
module \simple_soc.interconnect0.U$$0.decoder (wb_ram_instr_mem_bus__dat_w, wb_ram_instr_mem_bus__dat_r, wb_ram_instr_mem_bus__sel, wb_ram_instr_mem_bus__cyc, wb_ram_instr_mem_bus__stb, wb_ram_instr_mem_bus__we, wb_ram_instr_mem_bus__ack, wb_ram_instr_mem_bus__err, wb_ram_instr_mem_bus__cti, wb_ram_instr_mem_bus__bte, wb_ram_data_mem_bus__adr, wb_ram_data_mem_bus__dat_w, wb_ram_data_mem_bus__dat_r, wb_ram_data_mem_bus__sel, wb_ram_data_mem_bus__cyc, wb_ram_data_mem_bus__stb, wb_ram_data_mem_bus__we, wb_ram_data_mem_bus__ack, wb_ram_data_mem_bus__err, wb_ram_data_mem_bus__cti, wb_ram_data_mem_bus__bte
, wb_uart_csr_wishbone__adr, wb_uart_csr_wishbone__dat_w, wb_uart_csr_wishbone__dat_r, wb_uart_csr_wishbone__sel, wb_uart_csr_wishbone__cyc, wb_uart_csr_wishbone__stb, wb_uart_csr_wishbone__we, wb_uart_csr_wishbone__ack, wb_uart_csr_wishbone__err, wb_uart_csr_wishbone__cti, wb_uart_csr_wishbone__bte, bus__ack, bus__adr, bus__bte, bus__cti, bus__cyc, bus__dat_r, bus__dat_w, bus__err, bus__sel, bus__stb
, bus__we, wb_ram_instr_mem_bus__adr);
  reg \$auto$verilog_backend.cc:2253:dump_module$2  = 0;
  wire [30:0] \$1 ;
  wire \$10 ;
  wire \$12 ;
  wire \$14 ;
  wire \$16 ;
  wire \$18 ;
  wire [30:0] \$2 ;
  wire \$20 ;
  wire [30:0] \$4 ;
  wire [30:0] \$5 ;
  wire [30:0] \$7 ;
  wire [30:0] \$8 ;
  output bus__ack;
  wire bus__ack;
  input [29:0] bus__adr;
  wire [29:0] bus__adr;
  input [1:0] bus__bte;
  wire [1:0] bus__bte;
  input [2:0] bus__cti;
  wire [2:0] bus__cti;
  input bus__cyc;
  wire bus__cyc;
  output [31:0] bus__dat_r;
  reg [31:0] bus__dat_r;
  input [31:0] bus__dat_w;
  wire [31:0] bus__dat_w;
  output bus__err;
  wire bus__err;
  input [3:0] bus__sel;
  wire [3:0] bus__sel;
  input bus__stb;
  wire bus__stb;
  input bus__we;
  wire bus__we;
  input wb_ram_data_mem_bus__ack;
  wire wb_ram_data_mem_bus__ack;
  output [11:0] wb_ram_data_mem_bus__adr;
  wire [11:0] wb_ram_data_mem_bus__adr;
  output [1:0] wb_ram_data_mem_bus__bte;
  wire [1:0] wb_ram_data_mem_bus__bte;
  output [2:0] wb_ram_data_mem_bus__cti;
  wire [2:0] wb_ram_data_mem_bus__cti;
  output wb_ram_data_mem_bus__cyc;
  reg wb_ram_data_mem_bus__cyc;
  input [31:0] wb_ram_data_mem_bus__dat_r;
  wire [31:0] wb_ram_data_mem_bus__dat_r;
  output [31:0] wb_ram_data_mem_bus__dat_w;
  wire [31:0] wb_ram_data_mem_bus__dat_w;
  input wb_ram_data_mem_bus__err;
  wire wb_ram_data_mem_bus__err;
  output [3:0] wb_ram_data_mem_bus__sel;
  wire [3:0] wb_ram_data_mem_bus__sel;
  output wb_ram_data_mem_bus__stb;
  wire wb_ram_data_mem_bus__stb;
  output wb_ram_data_mem_bus__we;
  wire wb_ram_data_mem_bus__we;
  input wb_ram_instr_mem_bus__ack;
  wire wb_ram_instr_mem_bus__ack;
  output [15:0] wb_ram_instr_mem_bus__adr;
  wire [15:0] wb_ram_instr_mem_bus__adr;
  output [1:0] wb_ram_instr_mem_bus__bte;
  wire [1:0] wb_ram_instr_mem_bus__bte;
  output [2:0] wb_ram_instr_mem_bus__cti;
  wire [2:0] wb_ram_instr_mem_bus__cti;
  output wb_ram_instr_mem_bus__cyc;
  reg wb_ram_instr_mem_bus__cyc;
  input [31:0] wb_ram_instr_mem_bus__dat_r;
  wire [31:0] wb_ram_instr_mem_bus__dat_r;
  output [31:0] wb_ram_instr_mem_bus__dat_w;
  wire [31:0] wb_ram_instr_mem_bus__dat_w;
  input wb_ram_instr_mem_bus__err;
  wire wb_ram_instr_mem_bus__err;
  output [3:0] wb_ram_instr_mem_bus__sel;
  wire [3:0] wb_ram_instr_mem_bus__sel;
  output wb_ram_instr_mem_bus__stb;
  wire wb_ram_instr_mem_bus__stb;
  output wb_ram_instr_mem_bus__we;
  wire wb_ram_instr_mem_bus__we;
  input wb_uart_csr_wishbone__ack;
  wire wb_uart_csr_wishbone__ack;
  output [11:0] wb_uart_csr_wishbone__adr;
  wire [11:0] wb_uart_csr_wishbone__adr;
  output [1:0] wb_uart_csr_wishbone__bte;
  wire [1:0] wb_uart_csr_wishbone__bte;
  output [2:0] wb_uart_csr_wishbone__cti;
  wire [2:0] wb_uart_csr_wishbone__cti;
  output wb_uart_csr_wishbone__cyc;
  reg wb_uart_csr_wishbone__cyc;
  input [31:0] wb_uart_csr_wishbone__dat_r;
  wire [31:0] wb_uart_csr_wishbone__dat_r;
  output [31:0] wb_uart_csr_wishbone__dat_w;
  wire [31:0] wb_uart_csr_wishbone__dat_w;
  input wb_uart_csr_wishbone__err;
  wire wb_uart_csr_wishbone__err;
  output [3:0] wb_uart_csr_wishbone__sel;
  wire [3:0] wb_uart_csr_wishbone__sel;
  output wb_uart_csr_wishbone__stb;
  wire wb_uart_csr_wishbone__stb;
  output wb_uart_csr_wishbone__we;
  wire wb_uart_csr_wishbone__we;
  assign \$12  = \$10  | wb_ram_data_mem_bus__ack;
  assign \$14  = \$12  | wb_uart_csr_wishbone__ack;
  assign \$18  = \$16  | wb_ram_data_mem_bus__err;
  assign \$20  = \$18  | wb_uart_csr_wishbone__err;
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$2 ) begin end
    wb_ram_instr_mem_bus__cyc = 1'h0;
    casez (bus__adr)
      30'h0000????:
          wb_ram_instr_mem_bus__cyc = bus__cyc;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$2 ) begin end
    bus__dat_r = 32'd0;
    casez (bus__adr)
      30'h0000????:
          bus__dat_r = wb_ram_instr_mem_bus__dat_r;
      30'h04000???:
          bus__dat_r = wb_ram_data_mem_bus__dat_r;
      30'h3c000???:
          bus__dat_r = wb_uart_csr_wishbone__dat_r;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$2 ) begin end
    wb_ram_data_mem_bus__cyc = 1'h0;
    casez (bus__adr)
      30'h0000????:
          /* empty */;
      30'h04000???:
          wb_ram_data_mem_bus__cyc = bus__cyc;
    endcase
  end
  always @* begin
    if (\$auto$verilog_backend.cc:2253:dump_module$2 ) begin end
    wb_uart_csr_wishbone__cyc = 1'h0;
    casez (bus__adr)
      30'h0000????:
          /* empty */;
      30'h04000???:
          /* empty */;
      30'h3c000???:
          wb_uart_csr_wishbone__cyc = bus__cyc;
    endcase
  end
  assign \$1  = \$2 ;
  assign \$4  = \$5 ;
  assign \$7  = \$8 ;
  assign bus__err = \$20 ;
  assign bus__ack = \$14 ;
  assign wb_uart_csr_wishbone__bte = bus__bte;
  assign wb_uart_csr_wishbone__cti = bus__cti;
  assign wb_uart_csr_wishbone__stb = bus__stb;
  assign wb_uart_csr_wishbone__we = bus__we;
  assign wb_uart_csr_wishbone__sel = bus__sel;
  assign wb_uart_csr_wishbone__dat_w = bus__dat_w;
  assign wb_uart_csr_wishbone__adr = \$8 [11:0];
  assign wb_ram_data_mem_bus__bte = bus__bte;
  assign wb_ram_data_mem_bus__cti = bus__cti;
  assign wb_ram_data_mem_bus__stb = bus__stb;
  assign wb_ram_data_mem_bus__we = bus__we;
  assign wb_ram_data_mem_bus__sel = bus__sel;
  assign wb_ram_data_mem_bus__dat_w = bus__dat_w;
  assign wb_ram_data_mem_bus__adr = \$5 [11:0];
  assign wb_ram_instr_mem_bus__bte = bus__bte;
  assign wb_ram_instr_mem_bus__cti = bus__cti;
  assign wb_ram_instr_mem_bus__stb = bus__stb;
  assign wb_ram_instr_mem_bus__we = bus__we;
  assign wb_ram_instr_mem_bus__sel = bus__sel;
  assign wb_ram_instr_mem_bus__dat_w = bus__dat_w;
  assign wb_ram_instr_mem_bus__adr = \$2 [15:0];
  assign \$2  = { 1'h0, bus__adr };
  assign \$5  = { 1'h0, bus__adr };
  assign \$8  = { 1'h0, bus__adr };
  assign \$10  = wb_ram_instr_mem_bus__ack;
  assign \$16  = wb_ram_instr_mem_bus__err;
endmodule
