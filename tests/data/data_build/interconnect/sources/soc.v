/* Machine-generated using Migen */
module soc(
	output [29:0] ibus_adr,
	output [31:0] ibus_dat_w,
	input [31:0] ibus_dat_r,
	output [3:0] ibus_sel,
	output ibus_cyc,
	output ibus_stb,
	input ibus_ack,
	output ibus_we,
	output [2:0] ibus_cti,
	output [1:0] ibus_bte,
	input ibus_err,
	output [29:0] dbus_adr,
	output [31:0] dbus_dat_w,
	input [31:0] dbus_dat_r,
	output [3:0] dbus_sel,
	output dbus_cyc,
	output dbus_stb,
	input dbus_ack,
	output dbus_we,
	output [2:0] dbus_cti,
	output [1:0] dbus_bte,
	input dbus_err,
	output sim_serial_source_valid,
	input sim_serial_source_ready,
	output [7:0] sim_serial_source_data,
	input sim_serial_sink_valid,
	output sim_serial_sink_ready,
	input [7:0] sim_serial_sink_data,
	input [29:0] csr_wishbone_adr,
	input [31:0] csr_wishbone_dat_w,
	output reg [31:0] csr_wishbone_dat_r,
	input [3:0] csr_wishbone_sel,
	input csr_wishbone_cyc,
	input csr_wishbone_stb,
	output reg csr_wishbone_ack,
	input csr_wishbone_we,
	input [2:0] csr_wishbone_cti,
	input [1:0] csr_wishbone_bte,
	input csr_wishbone_err,
	input sys_clk,
	input sys_rst
);

reg reset = 1'd0;
reg [31:0] interrupt = 32'd0;
reg [31:0] vexriscv = 32'd0;
reg [31:0] timer0_load_storage = 32'd0;
reg timer0_load_re = 1'd0;
reg [31:0] timer0_reload_storage = 32'd0;
reg timer0_reload_re = 1'd0;
reg timer0_en_storage = 1'd0;
reg timer0_en_re = 1'd0;
reg timer0_update_value_storage = 1'd0;
reg timer0_update_value_re = 1'd0;
reg [31:0] timer0_value_status = 32'd0;
wire timer0_value_we;
reg timer0_value_re = 1'd0;
wire timer0_irq;
wire timer0_zero_status;
reg timer0_zero_pending = 1'd0;
wire timer0_zero_trigger;
reg timer0_zero_clear;
reg timer0_zero_trigger_d = 1'd0;
wire timer0_zero0;
wire timer0_status_status;
wire timer0_status_we;
reg timer0_status_re = 1'd0;
wire timer0_zero1;
wire timer0_pending_status;
wire timer0_pending_we;
reg timer0_pending_re = 1'd0;
reg timer0_pending_r = 1'd0;
wire timer0_zero2;
reg timer0_enable_storage = 1'd0;
reg timer0_enable_re = 1'd0;
reg [31:0] timer0_value = 32'd0;
wire sink_valid;
wire sink_ready;
wire sink_first;
wire sink_last;
wire [7:0] sink_payload_data;
wire source_valid;
wire source_ready;
reg source_first = 1'd0;
reg source_last = 1'd0;
wire [7:0] source_payload_data;
reg uart_rxtx_re;
wire [7:0] uart_rxtx_r;
reg uart_rxtx_we;
wire [7:0] uart_rxtx_w;
wire uart_txfull_status;
wire uart_txfull_we;
reg uart_txfull_re = 1'd0;
wire uart_rxempty_status;
wire uart_rxempty_we;
reg uart_rxempty_re = 1'd0;
wire uart_irq;
wire uart_tx_status;
reg uart_tx_pending = 1'd0;
wire uart_tx_trigger;
reg uart_tx_clear;
reg uart_tx_trigger_d = 1'd0;
wire uart_rx_status;
reg uart_rx_pending = 1'd0;
wire uart_rx_trigger;
reg uart_rx_clear;
reg uart_rx_trigger_d = 1'd0;
wire uart_tx0;
wire uart_rx0;
reg [1:0] uart_status_status;
wire uart_status_we;
reg uart_status_re = 1'd0;
wire uart_tx1;
wire uart_rx1;
reg [1:0] uart_pending_status;
wire uart_pending_we;
reg uart_pending_re = 1'd0;
reg [1:0] uart_pending_r = 2'd0;
wire uart_tx2;
wire uart_rx2;
reg [1:0] uart_enable_storage = 2'd0;
reg uart_enable_re = 1'd0;
wire uart_txempty_status;
wire uart_txempty_we;
reg uart_txempty_re = 1'd0;
wire uart_rxfull_status;
wire uart_rxfull_we;
reg uart_rxfull_re = 1'd0;
wire uart_uart_sink_valid;
wire uart_uart_sink_ready;
wire uart_uart_sink_first;
wire uart_uart_sink_last;
wire [7:0] uart_uart_sink_payload_data;
wire uart_uart_source_valid;
wire uart_uart_source_ready;
wire uart_uart_source_first;
wire uart_uart_source_last;
wire [7:0] uart_uart_source_payload_data;
wire uart_tx_fifo_sink_valid;
wire uart_tx_fifo_sink_ready;
reg uart_tx_fifo_sink_first = 1'd0;
reg uart_tx_fifo_sink_last = 1'd0;
wire [7:0] uart_tx_fifo_sink_payload_data;
wire uart_tx_fifo_source_valid;
wire uart_tx_fifo_source_ready;
wire uart_tx_fifo_source_first;
wire uart_tx_fifo_source_last;
wire [7:0] uart_tx_fifo_source_payload_data;
wire uart_tx_fifo_re;
reg uart_tx_fifo_readable = 1'd0;
wire uart_tx_fifo_syncfifo_we;
wire uart_tx_fifo_syncfifo_writable;
wire uart_tx_fifo_syncfifo_re;
wire uart_tx_fifo_syncfifo_readable;
wire [9:0] uart_tx_fifo_syncfifo_din;
wire [9:0] uart_tx_fifo_syncfifo_dout;
reg [4:0] uart_tx_fifo_level0 = 5'd0;
reg uart_tx_fifo_replace = 1'd0;
reg [3:0] uart_tx_fifo_produce = 4'd0;
reg [3:0] uart_tx_fifo_consume = 4'd0;
reg [3:0] uart_tx_fifo_wrport_adr;
wire [9:0] uart_tx_fifo_wrport_dat_r;
wire uart_tx_fifo_wrport_we;
wire [9:0] uart_tx_fifo_wrport_dat_w;
wire uart_tx_fifo_do_read;
wire [3:0] uart_tx_fifo_rdport_adr;
wire [9:0] uart_tx_fifo_rdport_dat_r;
wire uart_tx_fifo_rdport_re;
wire [4:0] uart_tx_fifo_level1;
wire [7:0] uart_tx_fifo_fifo_in_payload_data;
wire uart_tx_fifo_fifo_in_first;
wire uart_tx_fifo_fifo_in_last;
wire [7:0] uart_tx_fifo_fifo_out_payload_data;
wire uart_tx_fifo_fifo_out_first;
wire uart_tx_fifo_fifo_out_last;
wire uart_rx_fifo_sink_valid;
wire uart_rx_fifo_sink_ready;
wire uart_rx_fifo_sink_first;
wire uart_rx_fifo_sink_last;
wire [7:0] uart_rx_fifo_sink_payload_data;
wire uart_rx_fifo_source_valid;
wire uart_rx_fifo_source_ready;
wire uart_rx_fifo_source_first;
wire uart_rx_fifo_source_last;
wire [7:0] uart_rx_fifo_source_payload_data;
wire uart_rx_fifo_re;
reg uart_rx_fifo_readable = 1'd0;
wire uart_rx_fifo_syncfifo_we;
wire uart_rx_fifo_syncfifo_writable;
wire uart_rx_fifo_syncfifo_re;
wire uart_rx_fifo_syncfifo_readable;
wire [9:0] uart_rx_fifo_syncfifo_din;
wire [9:0] uart_rx_fifo_syncfifo_dout;
reg [4:0] uart_rx_fifo_level0 = 5'd0;
reg uart_rx_fifo_replace = 1'd0;
reg [3:0] uart_rx_fifo_produce = 4'd0;
reg [3:0] uart_rx_fifo_consume = 4'd0;
reg [3:0] uart_rx_fifo_wrport_adr;
wire [9:0] uart_rx_fifo_wrport_dat_r;
wire uart_rx_fifo_wrport_we;
wire [9:0] uart_rx_fifo_wrport_dat_w;
wire uart_rx_fifo_do_read;
wire [3:0] uart_rx_fifo_rdport_adr;
wire [9:0] uart_rx_fifo_rdport_dat_r;
wire uart_rx_fifo_rdport_re;
wire [4:0] uart_rx_fifo_level1;
wire [7:0] uart_rx_fifo_fifo_in_payload_data;
wire uart_rx_fifo_fifo_in_first;
wire uart_rx_fifo_fifo_in_last;
wire [7:0] uart_rx_fifo_fifo_out_payload_data;
wire uart_rx_fifo_fifo_out_first;
wire uart_rx_fifo_fifo_out_last;
reg [13:0] csr_master_adr = 14'd0;
reg csr_master_we = 1'd0;
reg [7:0] csr_master_dat_w = 8'd0;
wire [7:0] csr_master_dat_r;
wire [13:0] interface0_bank_bus_adr;
wire interface0_bank_bus_we;
wire [7:0] interface0_bank_bus_dat_w;
reg [7:0] interface0_bank_bus_dat_r = 8'd0;
reg csrbank0_load3_re;
wire [7:0] csrbank0_load3_r;
reg csrbank0_load3_we;
wire [7:0] csrbank0_load3_w;
reg csrbank0_load2_re;
wire [7:0] csrbank0_load2_r;
reg csrbank0_load2_we;
wire [7:0] csrbank0_load2_w;
reg csrbank0_load1_re;
wire [7:0] csrbank0_load1_r;
reg csrbank0_load1_we;
wire [7:0] csrbank0_load1_w;
reg csrbank0_load0_re;
wire [7:0] csrbank0_load0_r;
reg csrbank0_load0_we;
wire [7:0] csrbank0_load0_w;
reg csrbank0_reload3_re;
wire [7:0] csrbank0_reload3_r;
reg csrbank0_reload3_we;
wire [7:0] csrbank0_reload3_w;
reg csrbank0_reload2_re;
wire [7:0] csrbank0_reload2_r;
reg csrbank0_reload2_we;
wire [7:0] csrbank0_reload2_w;
reg csrbank0_reload1_re;
wire [7:0] csrbank0_reload1_r;
reg csrbank0_reload1_we;
wire [7:0] csrbank0_reload1_w;
reg csrbank0_reload0_re;
wire [7:0] csrbank0_reload0_r;
reg csrbank0_reload0_we;
wire [7:0] csrbank0_reload0_w;
reg csrbank0_en0_re;
wire csrbank0_en0_r;
reg csrbank0_en0_we;
wire csrbank0_en0_w;
reg csrbank0_update_value0_re;
wire csrbank0_update_value0_r;
reg csrbank0_update_value0_we;
wire csrbank0_update_value0_w;
reg csrbank0_value3_re;
wire [7:0] csrbank0_value3_r;
reg csrbank0_value3_we;
wire [7:0] csrbank0_value3_w;
reg csrbank0_value2_re;
wire [7:0] csrbank0_value2_r;
reg csrbank0_value2_we;
wire [7:0] csrbank0_value2_w;
reg csrbank0_value1_re;
wire [7:0] csrbank0_value1_r;
reg csrbank0_value1_we;
wire [7:0] csrbank0_value1_w;
reg csrbank0_value0_re;
wire [7:0] csrbank0_value0_r;
reg csrbank0_value0_we;
wire [7:0] csrbank0_value0_w;
reg csrbank0_ev_status_re;
wire csrbank0_ev_status_r;
reg csrbank0_ev_status_we;
wire csrbank0_ev_status_w;
reg csrbank0_ev_pending_re;
wire csrbank0_ev_pending_r;
reg csrbank0_ev_pending_we;
wire csrbank0_ev_pending_w;
reg csrbank0_ev_enable0_re;
wire csrbank0_ev_enable0_r;
reg csrbank0_ev_enable0_we;
wire csrbank0_ev_enable0_w;
wire csrbank0_sel;
wire [13:0] interface1_bank_bus_adr;
wire interface1_bank_bus_we;
wire [7:0] interface1_bank_bus_dat_w;
reg [7:0] interface1_bank_bus_dat_r = 8'd0;
reg csrbank1_txfull_re;
wire csrbank1_txfull_r;
reg csrbank1_txfull_we;
wire csrbank1_txfull_w;
reg csrbank1_rxempty_re;
wire csrbank1_rxempty_r;
reg csrbank1_rxempty_we;
wire csrbank1_rxempty_w;
reg csrbank1_ev_status_re;
wire [1:0] csrbank1_ev_status_r;
reg csrbank1_ev_status_we;
wire [1:0] csrbank1_ev_status_w;
reg csrbank1_ev_pending_re;
wire [1:0] csrbank1_ev_pending_r;
reg csrbank1_ev_pending_we;
wire [1:0] csrbank1_ev_pending_w;
reg csrbank1_ev_enable0_re;
wire [1:0] csrbank1_ev_enable0_r;
reg csrbank1_ev_enable0_we;
wire [1:0] csrbank1_ev_enable0_w;
reg csrbank1_txempty_re;
wire csrbank1_txempty_r;
reg csrbank1_txempty_we;
wire csrbank1_txempty_w;
reg csrbank1_rxfull_re;
wire csrbank1_rxfull_r;
reg csrbank1_rxfull_we;
wire csrbank1_rxfull_w;
wire csrbank1_sel;
reg [1:0] state = 2'd0;
reg [1:0] next_state;
reg [7:0] csr_master_dat_w_next_value0;
reg csr_master_dat_w_next_value_ce0;
reg [13:0] csr_master_adr_next_value1;
reg csr_master_adr_next_value_ce1;
reg csr_master_we_next_value2;
reg csr_master_we_next_value_ce2;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign timer0_zero_trigger = (timer0_value == 1'd0);
assign timer0_zero0 = timer0_zero_status;
assign timer0_zero1 = timer0_zero_pending;

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	timer0_zero_clear <= 1'd0;
	if ((timer0_pending_re & timer0_pending_r)) begin
		timer0_zero_clear <= 1'd1;
	end
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign timer0_irq = (timer0_pending_status & timer0_enable_storage);
assign timer0_zero_status = timer0_zero_trigger;
assign sim_serial_source_valid = sink_valid;
assign sim_serial_source_data = sink_payload_data;
assign sink_ready = sim_serial_source_ready;
assign source_valid = sim_serial_sink_valid;
assign source_payload_data = sim_serial_sink_data;
assign sim_serial_sink_ready = source_ready;
assign uart_uart_sink_valid = source_valid;
assign source_ready = uart_uart_sink_ready;
assign uart_uart_sink_first = source_first;
assign uart_uart_sink_last = source_last;
assign uart_uart_sink_payload_data = source_payload_data;
assign sink_valid = uart_uart_source_valid;
assign uart_uart_source_ready = sink_ready;
assign sink_first = uart_uart_source_first;
assign sink_last = uart_uart_source_last;
assign sink_payload_data = uart_uart_source_payload_data;
assign uart_tx_fifo_sink_valid = uart_rxtx_re;
assign uart_tx_fifo_sink_payload_data = uart_rxtx_r;
assign uart_uart_source_valid = uart_tx_fifo_source_valid;
assign uart_tx_fifo_source_ready = uart_uart_source_ready;
assign uart_uart_source_first = uart_tx_fifo_source_first;
assign uart_uart_source_last = uart_tx_fifo_source_last;
assign uart_uart_source_payload_data = uart_tx_fifo_source_payload_data;
assign uart_txfull_status = (~uart_tx_fifo_sink_ready);
assign uart_txempty_status = (~uart_tx_fifo_source_valid);
assign uart_tx_trigger = uart_tx_fifo_sink_ready;
assign uart_rx_fifo_sink_valid = uart_uart_sink_valid;
assign uart_uart_sink_ready = uart_rx_fifo_sink_ready;
assign uart_rx_fifo_sink_first = uart_uart_sink_first;
assign uart_rx_fifo_sink_last = uart_uart_sink_last;
assign uart_rx_fifo_sink_payload_data = uart_uart_sink_payload_data;
assign uart_rxtx_w = uart_rx_fifo_source_payload_data;
assign uart_rx_fifo_source_ready = (uart_rx_clear | (1'd0 & uart_rxtx_we));
assign uart_rxempty_status = (~uart_rx_fifo_source_valid);
assign uart_rxfull_status = (~uart_rx_fifo_sink_ready);
assign uart_rx_trigger = uart_rx_fifo_source_valid;
assign uart_tx0 = uart_tx_status;
assign uart_tx1 = uart_tx_pending;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	uart_tx_clear <= 1'd0;
	if ((uart_pending_re & uart_pending_r[0])) begin
		uart_tx_clear <= 1'd1;
	end
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end
assign uart_rx0 = uart_rx_status;
assign uart_rx1 = uart_rx_pending;

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	uart_rx_clear <= 1'd0;
	if ((uart_pending_re & uart_pending_r[1])) begin
		uart_rx_clear <= 1'd1;
	end
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end
assign uart_irq = ((uart_pending_status[0] & uart_enable_storage[0]) | (uart_pending_status[1] & uart_enable_storage[1]));
assign uart_tx_status = uart_tx_trigger;
assign uart_rx_status = uart_rx_trigger;
assign uart_tx_fifo_syncfifo_din = {uart_tx_fifo_fifo_in_last, uart_tx_fifo_fifo_in_first, uart_tx_fifo_fifo_in_payload_data};
assign {uart_tx_fifo_fifo_out_last, uart_tx_fifo_fifo_out_first, uart_tx_fifo_fifo_out_payload_data} = uart_tx_fifo_syncfifo_dout;
assign uart_tx_fifo_sink_ready = uart_tx_fifo_syncfifo_writable;
assign uart_tx_fifo_syncfifo_we = uart_tx_fifo_sink_valid;
assign uart_tx_fifo_fifo_in_first = uart_tx_fifo_sink_first;
assign uart_tx_fifo_fifo_in_last = uart_tx_fifo_sink_last;
assign uart_tx_fifo_fifo_in_payload_data = uart_tx_fifo_sink_payload_data;
assign uart_tx_fifo_source_valid = uart_tx_fifo_readable;
assign uart_tx_fifo_source_first = uart_tx_fifo_fifo_out_first;
assign uart_tx_fifo_source_last = uart_tx_fifo_fifo_out_last;
assign uart_tx_fifo_source_payload_data = uart_tx_fifo_fifo_out_payload_data;
assign uart_tx_fifo_re = uart_tx_fifo_source_ready;
assign uart_tx_fifo_syncfifo_re = (uart_tx_fifo_syncfifo_readable & ((~uart_tx_fifo_readable) | uart_tx_fifo_re));
assign uart_tx_fifo_level1 = (uart_tx_fifo_level0 + uart_tx_fifo_readable);

// synthesis translate_off
reg dummy_d_3;
// synthesis translate_on
always @(*) begin
	uart_tx_fifo_wrport_adr <= 4'd0;
	if (uart_tx_fifo_replace) begin
		uart_tx_fifo_wrport_adr <= (uart_tx_fifo_produce - 1'd1);
	end else begin
		uart_tx_fifo_wrport_adr <= uart_tx_fifo_produce;
	end
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end
assign uart_tx_fifo_wrport_dat_w = uart_tx_fifo_syncfifo_din;
assign uart_tx_fifo_wrport_we = (uart_tx_fifo_syncfifo_we & (uart_tx_fifo_syncfifo_writable | uart_tx_fifo_replace));
assign uart_tx_fifo_do_read = (uart_tx_fifo_syncfifo_readable & uart_tx_fifo_syncfifo_re);
assign uart_tx_fifo_rdport_adr = uart_tx_fifo_consume;
assign uart_tx_fifo_syncfifo_dout = uart_tx_fifo_rdport_dat_r;
assign uart_tx_fifo_rdport_re = uart_tx_fifo_do_read;
assign uart_tx_fifo_syncfifo_writable = (uart_tx_fifo_level0 != 5'd16);
assign uart_tx_fifo_syncfifo_readable = (uart_tx_fifo_level0 != 1'd0);
assign uart_rx_fifo_syncfifo_din = {uart_rx_fifo_fifo_in_last, uart_rx_fifo_fifo_in_first, uart_rx_fifo_fifo_in_payload_data};
assign {uart_rx_fifo_fifo_out_last, uart_rx_fifo_fifo_out_first, uart_rx_fifo_fifo_out_payload_data} = uart_rx_fifo_syncfifo_dout;
assign uart_rx_fifo_sink_ready = uart_rx_fifo_syncfifo_writable;
assign uart_rx_fifo_syncfifo_we = uart_rx_fifo_sink_valid;
assign uart_rx_fifo_fifo_in_first = uart_rx_fifo_sink_first;
assign uart_rx_fifo_fifo_in_last = uart_rx_fifo_sink_last;
assign uart_rx_fifo_fifo_in_payload_data = uart_rx_fifo_sink_payload_data;
assign uart_rx_fifo_source_valid = uart_rx_fifo_readable;
assign uart_rx_fifo_source_first = uart_rx_fifo_fifo_out_first;
assign uart_rx_fifo_source_last = uart_rx_fifo_fifo_out_last;
assign uart_rx_fifo_source_payload_data = uart_rx_fifo_fifo_out_payload_data;
assign uart_rx_fifo_re = uart_rx_fifo_source_ready;
assign uart_rx_fifo_syncfifo_re = (uart_rx_fifo_syncfifo_readable & ((~uart_rx_fifo_readable) | uart_rx_fifo_re));
assign uart_rx_fifo_level1 = (uart_rx_fifo_level0 + uart_rx_fifo_readable);

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	uart_rx_fifo_wrport_adr <= 4'd0;
	if (uart_rx_fifo_replace) begin
		uart_rx_fifo_wrport_adr <= (uart_rx_fifo_produce - 1'd1);
	end else begin
		uart_rx_fifo_wrport_adr <= uart_rx_fifo_produce;
	end
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end
assign uart_rx_fifo_wrport_dat_w = uart_rx_fifo_syncfifo_din;
assign uart_rx_fifo_wrport_we = (uart_rx_fifo_syncfifo_we & (uart_rx_fifo_syncfifo_writable | uart_rx_fifo_replace));
assign uart_rx_fifo_do_read = (uart_rx_fifo_syncfifo_readable & uart_rx_fifo_syncfifo_re);
assign uart_rx_fifo_rdport_adr = uart_rx_fifo_consume;
assign uart_rx_fifo_syncfifo_dout = uart_rx_fifo_rdport_dat_r;
assign uart_rx_fifo_rdport_re = uart_rx_fifo_do_read;
assign uart_rx_fifo_syncfifo_writable = (uart_rx_fifo_level0 != 5'd16);
assign uart_rx_fifo_syncfifo_readable = (uart_rx_fifo_level0 != 1'd0);
assign csrbank0_sel = (interface0_bank_bus_adr[13:7] == 1'd1);
assign csrbank0_load3_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_5;
// synthesis translate_on
always @(*) begin
	csrbank0_load3_re <= 1'd0;
	csrbank0_load3_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 1'd0))) begin
		csrbank0_load3_re <= interface0_bank_bus_we;
		csrbank0_load3_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_5 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_load2_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_6;
// synthesis translate_on
always @(*) begin
	csrbank0_load2_re <= 1'd0;
	csrbank0_load2_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 1'd1))) begin
		csrbank0_load2_re <= interface0_bank_bus_we;
		csrbank0_load2_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_6 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_load1_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_7;
// synthesis translate_on
always @(*) begin
	csrbank0_load1_re <= 1'd0;
	csrbank0_load1_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 2'd2))) begin
		csrbank0_load1_re <= interface0_bank_bus_we;
		csrbank0_load1_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_7 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_load0_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_8;
// synthesis translate_on
always @(*) begin
	csrbank0_load0_re <= 1'd0;
	csrbank0_load0_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 2'd3))) begin
		csrbank0_load0_re <= interface0_bank_bus_we;
		csrbank0_load0_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_8 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_reload3_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_9;
// synthesis translate_on
always @(*) begin
	csrbank0_reload3_re <= 1'd0;
	csrbank0_reload3_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 3'd4))) begin
		csrbank0_reload3_re <= interface0_bank_bus_we;
		csrbank0_reload3_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_9 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_reload2_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_10;
// synthesis translate_on
always @(*) begin
	csrbank0_reload2_re <= 1'd0;
	csrbank0_reload2_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 3'd5))) begin
		csrbank0_reload2_re <= interface0_bank_bus_we;
		csrbank0_reload2_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_10 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_reload1_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_11;
// synthesis translate_on
always @(*) begin
	csrbank0_reload1_re <= 1'd0;
	csrbank0_reload1_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 3'd6))) begin
		csrbank0_reload1_re <= interface0_bank_bus_we;
		csrbank0_reload1_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_11 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_reload0_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_12;
// synthesis translate_on
always @(*) begin
	csrbank0_reload0_re <= 1'd0;
	csrbank0_reload0_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 3'd7))) begin
		csrbank0_reload0_re <= interface0_bank_bus_we;
		csrbank0_reload0_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_12 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_en0_r = interface0_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_13;
// synthesis translate_on
always @(*) begin
	csrbank0_en0_re <= 1'd0;
	csrbank0_en0_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd8))) begin
		csrbank0_en0_re <= interface0_bank_bus_we;
		csrbank0_en0_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_13 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_update_value0_r = interface0_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_14;
// synthesis translate_on
always @(*) begin
	csrbank0_update_value0_re <= 1'd0;
	csrbank0_update_value0_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd9))) begin
		csrbank0_update_value0_re <= interface0_bank_bus_we;
		csrbank0_update_value0_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_14 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_value3_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_15;
// synthesis translate_on
always @(*) begin
	csrbank0_value3_re <= 1'd0;
	csrbank0_value3_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd10))) begin
		csrbank0_value3_re <= interface0_bank_bus_we;
		csrbank0_value3_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_15 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_value2_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_16;
// synthesis translate_on
always @(*) begin
	csrbank0_value2_re <= 1'd0;
	csrbank0_value2_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd11))) begin
		csrbank0_value2_re <= interface0_bank_bus_we;
		csrbank0_value2_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_16 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_value1_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_17;
// synthesis translate_on
always @(*) begin
	csrbank0_value1_re <= 1'd0;
	csrbank0_value1_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd12))) begin
		csrbank0_value1_re <= interface0_bank_bus_we;
		csrbank0_value1_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_17 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_value0_r = interface0_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_18;
// synthesis translate_on
always @(*) begin
	csrbank0_value0_re <= 1'd0;
	csrbank0_value0_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd13))) begin
		csrbank0_value0_re <= interface0_bank_bus_we;
		csrbank0_value0_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_18 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_ev_status_r = interface0_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_19;
// synthesis translate_on
always @(*) begin
	csrbank0_ev_status_re <= 1'd0;
	csrbank0_ev_status_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd14))) begin
		csrbank0_ev_status_re <= interface0_bank_bus_we;
		csrbank0_ev_status_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_19 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_ev_pending_r = interface0_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_20;
// synthesis translate_on
always @(*) begin
	csrbank0_ev_pending_re <= 1'd0;
	csrbank0_ev_pending_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 4'd15))) begin
		csrbank0_ev_pending_re <= interface0_bank_bus_we;
		csrbank0_ev_pending_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_20 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_ev_enable0_r = interface0_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_21;
// synthesis translate_on
always @(*) begin
	csrbank0_ev_enable0_re <= 1'd0;
	csrbank0_ev_enable0_we <= 1'd0;
	if ((csrbank0_sel & (interface0_bank_bus_adr[6:0] == 5'd16))) begin
		csrbank0_ev_enable0_re <= interface0_bank_bus_we;
		csrbank0_ev_enable0_we <= (~interface0_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_21 <= dummy_s;
// synthesis translate_on
end
assign csrbank0_load3_w = timer0_load_storage[31:24];
assign csrbank0_load2_w = timer0_load_storage[23:16];
assign csrbank0_load1_w = timer0_load_storage[15:8];
assign csrbank0_load0_w = timer0_load_storage[7:0];
assign csrbank0_reload3_w = timer0_reload_storage[31:24];
assign csrbank0_reload2_w = timer0_reload_storage[23:16];
assign csrbank0_reload1_w = timer0_reload_storage[15:8];
assign csrbank0_reload0_w = timer0_reload_storage[7:0];
assign csrbank0_en0_w = timer0_en_storage;
assign csrbank0_update_value0_w = timer0_update_value_storage;
assign csrbank0_value3_w = timer0_value_status[31:24];
assign csrbank0_value2_w = timer0_value_status[23:16];
assign csrbank0_value1_w = timer0_value_status[15:8];
assign csrbank0_value0_w = timer0_value_status[7:0];
assign timer0_value_we = csrbank0_value0_we;
assign timer0_status_status = timer0_zero0;
assign csrbank0_ev_status_w = timer0_status_status;
assign timer0_status_we = csrbank0_ev_status_we;
assign timer0_pending_status = timer0_zero1;
assign csrbank0_ev_pending_w = timer0_pending_status;
assign timer0_pending_we = csrbank0_ev_pending_we;
assign timer0_zero2 = timer0_enable_storage;
assign csrbank0_ev_enable0_w = timer0_enable_storage;
assign csrbank1_sel = (interface1_bank_bus_adr[13:7] == 1'd0);
assign uart_rxtx_r = interface1_bank_bus_dat_w[7:0];

// synthesis translate_off
reg dummy_d_22;
// synthesis translate_on
always @(*) begin
	uart_rxtx_re <= 1'd0;
	uart_rxtx_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 1'd0))) begin
		uart_rxtx_re <= interface1_bank_bus_we;
		uart_rxtx_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_22 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_txfull_r = interface1_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_23;
// synthesis translate_on
always @(*) begin
	csrbank1_txfull_re <= 1'd0;
	csrbank1_txfull_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 1'd1))) begin
		csrbank1_txfull_re <= interface1_bank_bus_we;
		csrbank1_txfull_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_23 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_rxempty_r = interface1_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_24;
// synthesis translate_on
always @(*) begin
	csrbank1_rxempty_re <= 1'd0;
	csrbank1_rxempty_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 2'd2))) begin
		csrbank1_rxempty_re <= interface1_bank_bus_we;
		csrbank1_rxempty_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_24 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_ev_status_r = interface1_bank_bus_dat_w[1:0];

// synthesis translate_off
reg dummy_d_25;
// synthesis translate_on
always @(*) begin
	csrbank1_ev_status_re <= 1'd0;
	csrbank1_ev_status_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 2'd3))) begin
		csrbank1_ev_status_re <= interface1_bank_bus_we;
		csrbank1_ev_status_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_25 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_ev_pending_r = interface1_bank_bus_dat_w[1:0];

// synthesis translate_off
reg dummy_d_26;
// synthesis translate_on
always @(*) begin
	csrbank1_ev_pending_re <= 1'd0;
	csrbank1_ev_pending_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 3'd4))) begin
		csrbank1_ev_pending_re <= interface1_bank_bus_we;
		csrbank1_ev_pending_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_26 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_ev_enable0_r = interface1_bank_bus_dat_w[1:0];

// synthesis translate_off
reg dummy_d_27;
// synthesis translate_on
always @(*) begin
	csrbank1_ev_enable0_re <= 1'd0;
	csrbank1_ev_enable0_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 3'd5))) begin
		csrbank1_ev_enable0_re <= interface1_bank_bus_we;
		csrbank1_ev_enable0_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_27 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_txempty_r = interface1_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_28;
// synthesis translate_on
always @(*) begin
	csrbank1_txempty_re <= 1'd0;
	csrbank1_txempty_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 3'd6))) begin
		csrbank1_txempty_re <= interface1_bank_bus_we;
		csrbank1_txempty_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_28 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_rxfull_r = interface1_bank_bus_dat_w[0];

// synthesis translate_off
reg dummy_d_29;
// synthesis translate_on
always @(*) begin
	csrbank1_rxfull_re <= 1'd0;
	csrbank1_rxfull_we <= 1'd0;
	if ((csrbank1_sel & (interface1_bank_bus_adr[6:0] == 3'd7))) begin
		csrbank1_rxfull_re <= interface1_bank_bus_we;
		csrbank1_rxfull_we <= (~interface1_bank_bus_we);
	end
// synthesis translate_off
	dummy_d_29 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_txfull_w = uart_txfull_status;
assign uart_txfull_we = csrbank1_txfull_we;
assign csrbank1_rxempty_w = uart_rxempty_status;
assign uart_rxempty_we = csrbank1_rxempty_we;

// synthesis translate_off
reg dummy_d_30;
// synthesis translate_on
always @(*) begin
	uart_status_status <= 2'd0;
	uart_status_status[0] <= uart_tx0;
	uart_status_status[1] <= uart_rx0;
// synthesis translate_off
	dummy_d_30 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_ev_status_w = uart_status_status[1:0];
assign uart_status_we = csrbank1_ev_status_we;

// synthesis translate_off
reg dummy_d_31;
// synthesis translate_on
always @(*) begin
	uart_pending_status <= 2'd0;
	uart_pending_status[0] <= uart_tx1;
	uart_pending_status[1] <= uart_rx1;
// synthesis translate_off
	dummy_d_31 <= dummy_s;
// synthesis translate_on
end
assign csrbank1_ev_pending_w = uart_pending_status[1:0];
assign uart_pending_we = csrbank1_ev_pending_we;
assign uart_tx2 = uart_enable_storage[0];
assign uart_rx2 = uart_enable_storage[1];
assign csrbank1_ev_enable0_w = uart_enable_storage[1:0];
assign csrbank1_txempty_w = uart_txempty_status;
assign uart_txempty_we = csrbank1_txempty_we;
assign csrbank1_rxfull_w = uart_rxfull_status;
assign uart_rxfull_we = csrbank1_rxfull_we;
assign interface0_bank_bus_adr = csr_master_adr;
assign interface1_bank_bus_adr = csr_master_adr;
assign interface0_bank_bus_we = csr_master_we;
assign interface1_bank_bus_we = csr_master_we;
assign interface0_bank_bus_dat_w = csr_master_dat_w;
assign interface1_bank_bus_dat_w = csr_master_dat_w;
assign csr_master_dat_r = (interface0_bank_bus_dat_r | interface1_bank_bus_dat_r);

// synthesis translate_off
reg dummy_d_32;
// synthesis translate_on
always @(*) begin
	csr_wishbone_dat_r <= 32'd0;
	csr_wishbone_ack <= 1'd0;
	next_state <= 2'd0;
	csr_master_dat_w_next_value0 <= 8'd0;
	csr_master_dat_w_next_value_ce0 <= 1'd0;
	csr_master_adr_next_value1 <= 14'd0;
	csr_master_adr_next_value_ce1 <= 1'd0;
	csr_master_we_next_value2 <= 1'd0;
	csr_master_we_next_value_ce2 <= 1'd0;
	next_state <= state;
	case (state)
		1'd1: begin
			csr_master_adr_next_value1 <= 1'd0;
			csr_master_adr_next_value_ce1 <= 1'd1;
			csr_master_we_next_value2 <= 1'd0;
			csr_master_we_next_value_ce2 <= 1'd1;
			next_state <= 2'd2;
		end
		2'd2: begin
			csr_wishbone_ack <= 1'd1;
			csr_wishbone_dat_r <= csr_master_dat_r;
			next_state <= 1'd0;
		end
		default: begin
			csr_master_dat_w_next_value0 <= csr_wishbone_dat_w;
			csr_master_dat_w_next_value_ce0 <= 1'd1;
			if ((csr_wishbone_cyc & csr_wishbone_stb)) begin
				csr_master_adr_next_value1 <= csr_wishbone_adr;
				csr_master_adr_next_value_ce1 <= 1'd1;
				csr_master_we_next_value2 <= (csr_wishbone_we & (csr_wishbone_sel != 1'd0));
				csr_master_we_next_value_ce2 <= 1'd1;
				next_state <= 1'd1;
			end
		end
	endcase
// synthesis translate_off
	dummy_d_32 <= dummy_s;
// synthesis translate_on
end

always @(posedge sys_clk) begin
	if (timer0_en_storage) begin
		if ((timer0_value == 1'd0)) begin
			timer0_value <= timer0_reload_storage;
		end else begin
			timer0_value <= (timer0_value - 1'd1);
		end
	end else begin
		timer0_value <= timer0_load_storage;
	end
	if (timer0_update_value_re) begin
		timer0_value_status <= timer0_value;
	end
	if (timer0_zero_clear) begin
		timer0_zero_pending <= 1'd0;
	end
	timer0_zero_trigger_d <= timer0_zero_trigger;
	if ((timer0_zero_trigger & (~timer0_zero_trigger_d))) begin
		timer0_zero_pending <= 1'd1;
	end
	if (uart_tx_clear) begin
		uart_tx_pending <= 1'd0;
	end
	uart_tx_trigger_d <= uart_tx_trigger;
	if ((uart_tx_trigger & (~uart_tx_trigger_d))) begin
		uart_tx_pending <= 1'd1;
	end
	if (uart_rx_clear) begin
		uart_rx_pending <= 1'd0;
	end
	uart_rx_trigger_d <= uart_rx_trigger;
	if ((uart_rx_trigger & (~uart_rx_trigger_d))) begin
		uart_rx_pending <= 1'd1;
	end
	if (uart_tx_fifo_syncfifo_re) begin
		uart_tx_fifo_readable <= 1'd1;
	end else begin
		if (uart_tx_fifo_re) begin
			uart_tx_fifo_readable <= 1'd0;
		end
	end
	if (((uart_tx_fifo_syncfifo_we & uart_tx_fifo_syncfifo_writable) & (~uart_tx_fifo_replace))) begin
		uart_tx_fifo_produce <= (uart_tx_fifo_produce + 1'd1);
	end
	if (uart_tx_fifo_do_read) begin
		uart_tx_fifo_consume <= (uart_tx_fifo_consume + 1'd1);
	end
	if (((uart_tx_fifo_syncfifo_we & uart_tx_fifo_syncfifo_writable) & (~uart_tx_fifo_replace))) begin
		if ((~uart_tx_fifo_do_read)) begin
			uart_tx_fifo_level0 <= (uart_tx_fifo_level0 + 1'd1);
		end
	end else begin
		if (uart_tx_fifo_do_read) begin
			uart_tx_fifo_level0 <= (uart_tx_fifo_level0 - 1'd1);
		end
	end
	if (uart_rx_fifo_syncfifo_re) begin
		uart_rx_fifo_readable <= 1'd1;
	end else begin
		if (uart_rx_fifo_re) begin
			uart_rx_fifo_readable <= 1'd0;
		end
	end
	if (((uart_rx_fifo_syncfifo_we & uart_rx_fifo_syncfifo_writable) & (~uart_rx_fifo_replace))) begin
		uart_rx_fifo_produce <= (uart_rx_fifo_produce + 1'd1);
	end
	if (uart_rx_fifo_do_read) begin
		uart_rx_fifo_consume <= (uart_rx_fifo_consume + 1'd1);
	end
	if (((uart_rx_fifo_syncfifo_we & uart_rx_fifo_syncfifo_writable) & (~uart_rx_fifo_replace))) begin
		if ((~uart_rx_fifo_do_read)) begin
			uart_rx_fifo_level0 <= (uart_rx_fifo_level0 + 1'd1);
		end
	end else begin
		if (uart_rx_fifo_do_read) begin
			uart_rx_fifo_level0 <= (uart_rx_fifo_level0 - 1'd1);
		end
	end
	interface0_bank_bus_dat_r <= 1'd0;
	if (csrbank0_sel) begin
		case (interface0_bank_bus_adr[6:0])
			1'd0: begin
				interface0_bank_bus_dat_r <= csrbank0_load3_w;
			end
			1'd1: begin
				interface0_bank_bus_dat_r <= csrbank0_load2_w;
			end
			2'd2: begin
				interface0_bank_bus_dat_r <= csrbank0_load1_w;
			end
			2'd3: begin
				interface0_bank_bus_dat_r <= csrbank0_load0_w;
			end
			3'd4: begin
				interface0_bank_bus_dat_r <= csrbank0_reload3_w;
			end
			3'd5: begin
				interface0_bank_bus_dat_r <= csrbank0_reload2_w;
			end
			3'd6: begin
				interface0_bank_bus_dat_r <= csrbank0_reload1_w;
			end
			3'd7: begin
				interface0_bank_bus_dat_r <= csrbank0_reload0_w;
			end
			4'd8: begin
				interface0_bank_bus_dat_r <= csrbank0_en0_w;
			end
			4'd9: begin
				interface0_bank_bus_dat_r <= csrbank0_update_value0_w;
			end
			4'd10: begin
				interface0_bank_bus_dat_r <= csrbank0_value3_w;
			end
			4'd11: begin
				interface0_bank_bus_dat_r <= csrbank0_value2_w;
			end
			4'd12: begin
				interface0_bank_bus_dat_r <= csrbank0_value1_w;
			end
			4'd13: begin
				interface0_bank_bus_dat_r <= csrbank0_value0_w;
			end
			4'd14: begin
				interface0_bank_bus_dat_r <= csrbank0_ev_status_w;
			end
			4'd15: begin
				interface0_bank_bus_dat_r <= csrbank0_ev_pending_w;
			end
			5'd16: begin
				interface0_bank_bus_dat_r <= csrbank0_ev_enable0_w;
			end
		endcase
	end
	if (csrbank0_load3_re) begin
		timer0_load_storage[31:24] <= csrbank0_load3_r;
	end
	if (csrbank0_load2_re) begin
		timer0_load_storage[23:16] <= csrbank0_load2_r;
	end
	if (csrbank0_load1_re) begin
		timer0_load_storage[15:8] <= csrbank0_load1_r;
	end
	if (csrbank0_load0_re) begin
		timer0_load_storage[7:0] <= csrbank0_load0_r;
	end
	timer0_load_re <= csrbank0_load0_re;
	if (csrbank0_reload3_re) begin
		timer0_reload_storage[31:24] <= csrbank0_reload3_r;
	end
	if (csrbank0_reload2_re) begin
		timer0_reload_storage[23:16] <= csrbank0_reload2_r;
	end
	if (csrbank0_reload1_re) begin
		timer0_reload_storage[15:8] <= csrbank0_reload1_r;
	end
	if (csrbank0_reload0_re) begin
		timer0_reload_storage[7:0] <= csrbank0_reload0_r;
	end
	timer0_reload_re <= csrbank0_reload0_re;
	if (csrbank0_en0_re) begin
		timer0_en_storage <= csrbank0_en0_r;
	end
	timer0_en_re <= csrbank0_en0_re;
	if (csrbank0_update_value0_re) begin
		timer0_update_value_storage <= csrbank0_update_value0_r;
	end
	timer0_update_value_re <= csrbank0_update_value0_re;
	timer0_value_re <= csrbank0_value0_re;
	timer0_status_re <= csrbank0_ev_status_re;
	if (csrbank0_ev_pending_re) begin
		timer0_pending_r <= csrbank0_ev_pending_r;
	end
	timer0_pending_re <= csrbank0_ev_pending_re;
	if (csrbank0_ev_enable0_re) begin
		timer0_enable_storage <= csrbank0_ev_enable0_r;
	end
	timer0_enable_re <= csrbank0_ev_enable0_re;
	interface1_bank_bus_dat_r <= 1'd0;
	if (csrbank1_sel) begin
		case (interface1_bank_bus_adr[6:0])
			1'd0: begin
				interface1_bank_bus_dat_r <= uart_rxtx_w;
			end
			1'd1: begin
				interface1_bank_bus_dat_r <= csrbank1_txfull_w;
			end
			2'd2: begin
				interface1_bank_bus_dat_r <= csrbank1_rxempty_w;
			end
			2'd3: begin
				interface1_bank_bus_dat_r <= csrbank1_ev_status_w;
			end
			3'd4: begin
				interface1_bank_bus_dat_r <= csrbank1_ev_pending_w;
			end
			3'd5: begin
				interface1_bank_bus_dat_r <= csrbank1_ev_enable0_w;
			end
			3'd6: begin
				interface1_bank_bus_dat_r <= csrbank1_txempty_w;
			end
			3'd7: begin
				interface1_bank_bus_dat_r <= csrbank1_rxfull_w;
			end
		endcase
	end
	uart_txfull_re <= csrbank1_txfull_re;
	uart_rxempty_re <= csrbank1_rxempty_re;
	uart_status_re <= csrbank1_ev_status_re;
	if (csrbank1_ev_pending_re) begin
		uart_pending_r[1:0] <= csrbank1_ev_pending_r;
	end
	uart_pending_re <= csrbank1_ev_pending_re;
	if (csrbank1_ev_enable0_re) begin
		uart_enable_storage[1:0] <= csrbank1_ev_enable0_r;
	end
	uart_enable_re <= csrbank1_ev_enable0_re;
	uart_txempty_re <= csrbank1_txempty_re;
	uart_rxfull_re <= csrbank1_rxfull_re;
	state <= next_state;
	if (csr_master_dat_w_next_value_ce0) begin
		csr_master_dat_w <= csr_master_dat_w_next_value0;
	end
	if (csr_master_adr_next_value_ce1) begin
		csr_master_adr <= csr_master_adr_next_value1;
	end
	if (csr_master_we_next_value_ce2) begin
		csr_master_we <= csr_master_we_next_value2;
	end
	if (sys_rst) begin
		timer0_load_storage <= 32'd0;
		timer0_load_re <= 1'd0;
		timer0_reload_storage <= 32'd0;
		timer0_reload_re <= 1'd0;
		timer0_en_storage <= 1'd0;
		timer0_en_re <= 1'd0;
		timer0_update_value_storage <= 1'd0;
		timer0_update_value_re <= 1'd0;
		timer0_value_status <= 32'd0;
		timer0_value_re <= 1'd0;
		timer0_zero_pending <= 1'd0;
		timer0_zero_trigger_d <= 1'd0;
		timer0_status_re <= 1'd0;
		timer0_pending_re <= 1'd0;
		timer0_pending_r <= 1'd0;
		timer0_enable_storage <= 1'd0;
		timer0_enable_re <= 1'd0;
		timer0_value <= 32'd0;
		uart_txfull_re <= 1'd0;
		uart_rxempty_re <= 1'd0;
		uart_tx_pending <= 1'd0;
		uart_tx_trigger_d <= 1'd0;
		uart_rx_pending <= 1'd0;
		uart_rx_trigger_d <= 1'd0;
		uart_status_re <= 1'd0;
		uart_pending_re <= 1'd0;
		uart_pending_r <= 2'd0;
		uart_enable_storage <= 2'd0;
		uart_enable_re <= 1'd0;
		uart_txempty_re <= 1'd0;
		uart_rxfull_re <= 1'd0;
		uart_tx_fifo_readable <= 1'd0;
		uart_tx_fifo_level0 <= 5'd0;
		uart_tx_fifo_produce <= 4'd0;
		uart_tx_fifo_consume <= 4'd0;
		uart_rx_fifo_readable <= 1'd0;
		uart_rx_fifo_level0 <= 5'd0;
		uart_rx_fifo_produce <= 4'd0;
		uart_rx_fifo_consume <= 4'd0;
		csr_master_we <= 1'd0;
		state <= 2'd0;
	end
end

reg [9:0] storage[0:15];
reg [9:0] memdat;
reg [9:0] memdat_1;
always @(posedge sys_clk) begin
	if (uart_tx_fifo_wrport_we)
		storage[uart_tx_fifo_wrport_adr] <= uart_tx_fifo_wrport_dat_w;
	memdat <= storage[uart_tx_fifo_wrport_adr];
end

always @(posedge sys_clk) begin
	if (uart_tx_fifo_rdport_re)
		memdat_1 <= storage[uart_tx_fifo_rdport_adr];
end

assign uart_tx_fifo_wrport_dat_r = memdat;
assign uart_tx_fifo_rdport_dat_r = memdat_1;

reg [9:0] storage_1[0:15];
reg [9:0] memdat_2;
reg [9:0] memdat_3;
always @(posedge sys_clk) begin
	if (uart_rx_fifo_wrport_we)
		storage_1[uart_rx_fifo_wrport_adr] <= uart_rx_fifo_wrport_dat_w;
	memdat_2 <= storage_1[uart_rx_fifo_wrport_adr];
end

always @(posedge sys_clk) begin
	if (uart_rx_fifo_rdport_re)
		memdat_3 <= storage_1[uart_rx_fifo_rdport_adr];
end

assign uart_rx_fifo_wrport_dat_r = memdat_2;
assign uart_rx_fifo_rdport_dat_r = memdat_3;

VexRiscv VexRiscv(
	.clk(sys_clk),
	.dBusWishbone_ACK(dbus_ack),
	.dBusWishbone_DAT_MISO(dbus_dat_r),
	.dBusWishbone_ERR(dbus_err),
	.externalInterruptArray(interrupt),
	.externalResetVector(vexriscv),
	.iBusWishbone_ACK(ibus_ack),
	.iBusWishbone_DAT_MISO(ibus_dat_r),
	.iBusWishbone_ERR(ibus_err),
	.reset((sys_rst | reset)),
	.softwareInterrupt(1'd0),
	.timerInterrupt(1'd0),
	.dBusWishbone_ADR(dbus_adr),
	.dBusWishbone_BTE(dbus_bte),
	.dBusWishbone_CTI(dbus_cti),
	.dBusWishbone_CYC(dbus_cyc),
	.dBusWishbone_DAT_MOSI(dbus_dat_w),
	.dBusWishbone_SEL(dbus_sel),
	.dBusWishbone_STB(dbus_stb),
	.dBusWishbone_WE(dbus_we),
	.iBusWishbone_ADR(ibus_adr),
	.iBusWishbone_BTE(ibus_bte),
	.iBusWishbone_CTI(ibus_cti),
	.iBusWishbone_CYC(ibus_cyc),
	.iBusWishbone_DAT_MOSI(ibus_dat_w),
	.iBusWishbone_SEL(ibus_sel),
	.iBusWishbone_STB(ibus_stb),
	.iBusWishbone_WE(ibus_we)
);

endmodule
