// Copyright (c) 2025 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

module manager_axi (
    input wire clk,
    input wire rst,

    input wire example_ifaceAWREADY,
    output reg [31:0] example_ifaceAWADDR,
    output reg example_ifaceAWVALID,

    input wire example_ifaceWREADY,
    output reg [31:0] example_ifaceWDATA,
    output reg example_ifaceWVALID,

    output reg  example_ifaceBREADY,
    input  wire example_ifaceBVALID,

    input wire example_ifaceARREADY,
    output reg [31:0] example_ifaceARADDR,
    output reg example_ifaceARVALID,

    output reg example_ifaceRREADY,
    input wire [31:0] example_ifaceRDATA,
    input wire example_ifaceRVALID
);

  //SIGNALS START
  reg send_write_request;
  reg send_read_request;

  always @(posedge clk or negedge rst) begin
    if (!rst) begin
      send_write_request <= 0;
      send_read_request  <= 0;
    end else if (clk) begin
      if (send_write_request && example_ifaceBREADY && example_ifaceBVALID) send_write_request <= 0;
      if (send_read_request && example_ifaceRREADY && example_ifaceRVALID) send_read_request <= 0;
    end
  end
  //SIGNAlS END


  //WRITE START
  //TODO: implement it as FSM?
  reg [1:0] write_addr_data_sent;  //[0] is addr, [1] is data
  assign example_ifaceBREADY = &write_addr_data_sent;

  always @(posedge clk or negedge rst) begin
    if (!rst) begin
      example_ifaceAWVALID <= 0;
      example_ifaceWVALID  <= 0;
      write_addr_data_sent <= 2'b0;
    end else if (clk) begin
      if (!write_addr_data_sent[0] && send_write_request) begin
        example_ifaceAWADDR  <= 1234;
        example_ifaceAWVALID <= 1;
      end else example_ifaceAWVALID <= 0;

      if (!write_addr_data_sent[0] && example_ifaceAWREADY && example_ifaceAWVALID) begin
        write_addr_data_sent[0] <= 1;
      end

      if (!write_addr_data_sent[1] && send_write_request) begin
        example_ifaceWDATA  <= 4321;
        example_ifaceWVALID <= 1;
      end else example_ifaceWVALID <= 0;

      if (!write_addr_data_sent[1] && example_ifaceWREADY && example_ifaceAWVALID) begin
        write_addr_data_sent[1] <= 1;
      end

      if (example_ifaceBVALID) begin
        write_addr_data_sent <= 2'b0;
      end
    end
  end
  //END WRITE

  //READ
  reg [31:0] recived_data;
  reg recived_data_valid;

  always @(posedge clk or negedge rst) begin
    if (!rst) begin
      example_ifaceARVALID <= 0;
      example_ifaceRREADY  <= 0;
    end else if (clk) begin
      if (send_read_request) begin
        example_ifaceARADDR  <= 1235;
        example_ifaceARVALID <= 1;
        example_ifaceRREADY  <= 1;
      end else example_ifaceARVALID <= 0;

      if (send_read_request && example_ifaceARREADY) begin
        send_read_request <= 0;
      end

      if (example_ifaceRREADY && example_ifaceRVALID) begin
        example_ifaceRREADY <= 0;
      end
    end
  end

  always @(posedge clk or negedge rst) begin
    if (!rst) begin
      recived_data_valid <= 0;
      recived_data <= 0;
    end else if (clk) begin
      if (example_ifaceRVALID) begin
        recived_data <= example_ifaceRDATA;
        recived_data_valid <= 1;
      end
    end
  end
  //END_READ


endmodule
