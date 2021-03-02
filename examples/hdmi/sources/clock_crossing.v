// Copyright (C) 2021  Antmicro
// SPDX-License-Identifier: Apache-2.0
module cdc_flag (
    input wire clkA, input wire A, input wire clkB, output wire B
);

reg A_reg;

initial A_reg = 0;

always @(posedge clkA)
    if (A)
        A_reg = ~A_reg;

(* ASYNC_REG = "TRUE" *) reg [2:0] B_reg;

initial B_reg = 0;

always @(posedge clkB)
    B_reg = {B_reg[1:0], A_reg};

assign B = (B_reg[2] != B_reg[1]);

endmodule
