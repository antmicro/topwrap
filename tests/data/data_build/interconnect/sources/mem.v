module mem #(
	parameter depth = 256,
	parameter memfile = ""
)(
	input [29:0] mem_bus_adr,
	input [31:0] mem_bus_dat_w,
	output [31:0] mem_bus_dat_r,
	input [3:0] mem_bus_sel,
	input mem_bus_cyc,
	input mem_bus_stb,
	output reg mem_bus_ack,
	input mem_bus_we,
	input [2:0] mem_bus_cti,
	input [1:0] mem_bus_bte,
	input mem_bus_err,
	input sys_clk,
	input sys_rst
);

localparam aw = $clog2(depth);

reg adr_burst = 1'd0;
wire [aw-1:0] adr;
wire [31:0] dat_r;
reg [3:0] we;
wire [31:0] dat_w;


always @(*) begin
	we <= 4'd0;
	we[0] <= (((mem_bus_cyc & mem_bus_stb) & mem_bus_we) & mem_bus_sel[0]);
	we[1] <= (((mem_bus_cyc & mem_bus_stb) & mem_bus_we) & mem_bus_sel[1]);
	we[2] <= (((mem_bus_cyc & mem_bus_stb) & mem_bus_we) & mem_bus_sel[2]);
	we[3] <= (((mem_bus_cyc & mem_bus_stb) & mem_bus_we) & mem_bus_sel[3]);
end
assign adr = mem_bus_adr[aw-1:0];
assign mem_bus_dat_r = dat_r;
assign dat_w = mem_bus_dat_w;

always @(posedge sys_clk) begin
	mem_bus_ack <= 1'd0;
	if (((mem_bus_cyc & mem_bus_stb) & ((~mem_bus_ack) | adr_burst))) begin
		mem_bus_ack <= 1'd1;
	end
	if (sys_rst) begin
		mem_bus_ack <= 1'd0;
	end
end

reg [31:0] mem[0:depth-1];
reg [aw-1:0] memadr;
always @(posedge sys_clk) begin
	if (we[0])
		mem[adr][7:0] <= dat_w[7:0];
	if (we[1])
		mem[adr][15:8] <= dat_w[15:8];
	if (we[2])
		mem[adr][23:16] <= dat_w[23:16];
	if (we[3])
		mem[adr][31:24] <= dat_w[31:24];
	memadr <= adr;
end

assign dat_r = mem[memadr];

initial begin
	$readmemh(memfile, mem);
end

endmodule
