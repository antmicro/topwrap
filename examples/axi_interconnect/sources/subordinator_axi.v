// Copyright (c) 2025 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

module subordinator_axi (
    input wire clk,
    input wire rst,

    output reg example_ifaceAWREADY,
    input wire [31:0] example_ifaceAWADDR,
    input wire example_ifaceAWVALID,

    output reg example_ifaceWREADY,
    input wire [31:0] example_ifaceWDATA,
    input wire example_ifaceWVALID,

    input  wire example_ifaceBREADY,
    output reg  example_ifaceBVALID,

    output reg example_ifaceARREADY,
    input wire [31:0] example_ifaceARADDR,
    input wire example_ifaceARVALID,

    input wire example_ifaceRREADY,
    output reg [31:0] example_ifaceRDATA,
    output reg example_ifaceRVALID
);

  // first bit means that address was received
  // second bit means that data was received
  reg [1:0] write_addr_data_recived;
  wire write_recived;
  assign write_recived = &write_addr_data_recived;

  reg [31:0] write_addr;
  reg [31:0] write_data;

  always @(posedge clk or negedge rst) begin
    if (!rst) begin
      write_addr_data_recived <= 2'b0;
    end else if (clk) begin
      if (example_ifaceAWVALID) begin
        write_addr_data_recived[0] <= 1;
        write_addr <= example_ifaceAWADDR;
      end

      if (example_ifaceWVALID) begin
        write_addr_data_recived[1] <= 1;
        write_data <= example_ifaceWDATA;
      end
    end
  end

  assign example_ifaceBVALID  = write_recived;
  assign example_ifaceAWREADY = ~write_addr_data_recived[0];
  assign example_ifaceWREADY  = ~write_addr_data_recived[1];

  always @(posedge clk or negedge rst) begin
    if (!rst) begin
      example_ifaceARREADY <= 1;
      example_ifaceRVALID  <= 0;
    end else if (clk) begin
      if (example_ifaceARVALID) begin
        example_ifaceARREADY <= 0;
        example_ifaceRDATA   <= 1111;
        example_ifaceRVALID  <= 1;
      end else begin
        example_ifaceRVALID  <= 0;
        example_ifaceARREADY <= 1;
      end
    end
  end



endmodule
