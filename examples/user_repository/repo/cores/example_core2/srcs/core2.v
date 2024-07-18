`timescale 1ns / 1ps

module mod_b (
    input  wire in_1,
    input  wire in_2,
    output reg out_1,
    output wire c_tready,
    input wire c_tvalid,
    input wire [31:0] c_tdata,
    input wire [3:0] c_tkeep
);

endmodule
