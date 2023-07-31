// Copyright (C) 2023 Antmicro
// SPDX-License-Identifier: Apache-2.0

`timescale 1ns / 1ps

module obuf (
    input  wire clk,
    input  wire rst,
    input  wire oe,
    input  wire a,
    output reg z
);
  always@(posedge clk or posedge rst) begin : proc_input_buffer
    if (rst) begin
      z <= 1'b0;
    end else begin
      if (oe) begin
        z <= a;
      end else begin
        z <= 1'bz;
      end
    end
  end

endmodule

