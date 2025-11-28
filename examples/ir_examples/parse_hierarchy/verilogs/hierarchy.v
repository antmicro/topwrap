// Copyright (c) 2026 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

module D (
    input d_in,
    output logic d_out
);
    always_comb d_out = d_in;
endmodule


module C (
    input c_in,
    output c_out
);
    parameter bit Cparam_bit = 1'b0;
    parameter string Cparam_str = "";
    D dinst(.d_in(c_in), .d_out(c_out));
endmodule

module B (
    input b_in,
    output logic b_out
);
    parameter bit Bparam = 1'b0;
    always @(*) begin
        b_out = b_in;
    end
endmodule


module A (
    input clk,
    input a_b_in,
    input a_c_in,
    input [7:0] a_data_in,
    input logicdriver,
    output [1:0] a_out,
    output a_b_out,
    output [2:0] a_b_ext_out,
    output [2:0] a_b_ext_bitsel_out,
    output a_bit_sel_out,
    output [2:0] a_range_sel_out,
    output selfdriven_out,
    output [1:0] fordriven_out,
    output logic clocked_out
);
    logic [16:0] selfdriven;
    localparam int PARAM1 = 1;
    wire undriven;
    logic b_in;
    always @* b_in = a_b_in;
    wire b_out;
    logic c_in;
    assign c_in = a_c_in;
    wire c_out;
    assign a_out = {b_out, c_out};
    assign a_b_out = {b_out};
    assign a_b_ext_out = {1'b0, 1'b1, b_out};
    assign a_b_ext_bitsel_out[2:1] = {1'b0, b_out};
    assign a_b_ext_bitsel_out[0] = b_out;
    assign a_bit_sel_out = a_data_in[3];
    assign a_range_sel_out = a_data_in[5:3];
    assign selfdriven[0] = a_data_in[0];
    for(genvar i = 0; i < 15; i++) begin : gen_selfdriven
        assign selfdriven[i+1] = selfdriven[i];
    end
    assign selfdriven_out = selfdriven[15];
    B #(1'b1) binst(.b_in(~b_in), .b_out(b_out));
    C cinst(.c_in(c_in), .c_out(c_out));
    C cinst2(.c_in(undriven), .c_out());
    localparam int CONSTS = {1'b0, 1'b1};
    for (genvar i = 0; i < 2; i++) begin : genfor
        C #(CONSTS[i], "tab[i]") genfor_cinst(.c_in(c_in), .c_out(fordriven_out[i]));
    end
    always @(posedge clk) begin
        clocked_out <= ~clocked_out;
        if(logicdriver) begin
            clocked_out <= 1'b1;
        end
    end
endmodule
