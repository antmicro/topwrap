/* Machine-generated using Migen */
module crg(
	input clk100,
	output sys_clk,
	output sys_rst
);

wire por_clk;
reg int_rst = 1'd1;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign sys_clk = clk100;
assign por_clk = clk100;
assign sys_rst = int_rst;

always @(posedge por_clk) begin
	int_rst <= 1'd0;
end

endmodule
