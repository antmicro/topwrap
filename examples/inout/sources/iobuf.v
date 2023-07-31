// Copyright (C) 2023 Antmicro
// SPDX-License-Identifier: Apache-2.0

`timescale 1ns / 1ps

module iobuf (
    input  wire clk,
    input  wire rst,
    input  wire a,
    inout  wire z,
    output wire y,
    input  wire oe
);

  ibuf xibuf (
      .clk(clk),
      .rst(rst),
      .a  (z),
      .z  (y)
  );

  obuf xobuf (
      .clk(clk),
      .rst(rst),
      .oe (oe),
      .a  (a),
      .z  (z)
  );

endmodule

