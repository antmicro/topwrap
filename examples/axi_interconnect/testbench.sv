`timescale 1ps / 1ps

parameter integer CLK_PEROID = 4;

module tb;
  reg clk;
  reg rst;

  always #(CLK_PEROID / 2) clk = !clk;

  axi_interconnect_example dut (
      .clk(clk),
      .rst(rst)
  );

  initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb);
  end

  initial begin
    clk = 0;
    rst = 0;
    #5 rst = 1;
  end

  initial begin
    fork
      begin
        wait (dut.axi_interconnect.o_manager_axi_example_iface_bvalid == 1);
        $finish();
      end
      begin
        #200;
        $fatal("timeout, bvalid never arrived");
      end
    join_any
    disable fork;
  end

  initial begin
    #6;
    dut.manager_axi.send_read_request = 1;
    #35 dut.manager_axi.send_write_request = 1;
  end

  int araddr_value;
  initial begin
    wait (dut.axi_interconnect.i_manager_axi_example_iface_arvalid == 1);
    araddr_value = dut.axi_interconnect.i_manager_axi_example_iface_araddr;
    #(CLK_PEROID * 3);
    assert (dut.axi_interconnect.o_subordinator_axi_example_iface_arvalid == 1);
    assert (araddr_value == dut.axi_interconnect.o_subordinator_axi_example_iface_araddr);
  end

  int rdata_value;
  initial begin
    wait (dut.axi_interconnect.i_subordinator_axi_example_iface_rvalid == 1);
    rdata_value = dut.axi_interconnect.i_subordinator_axi_example_iface_rdata;
    #(CLK_PEROID * 0);
    assert (dut.axi_interconnect.o_manager_axi_example_iface_rvalid == 1);
    assert (rdata_value == dut.axi_interconnect.o_manager_axi_example_iface_rdata);
  end

  int awvalid_value;
  initial begin
    wait (dut.axi_interconnect.i_manager_axi_example_iface_awvalid == 1);
    awvalid_value = dut.axi_interconnect.i_manager_axi_example_iface_awaddr;
    #(CLK_PEROID * 3);
    assert (dut.axi_interconnect.o_subordinator_axi_example_iface_awvalid == 1);
    assert (awvalid_value == dut.axi_interconnect.o_subordinator_axi_example_iface_awaddr);
  end

  int wvalid_value;
  initial begin
    wait (dut.axi_interconnect.i_manager_axi_example_iface_wvalid == 1);
    wvalid_value = dut.axi_interconnect.i_manager_axi_example_iface_wdata;
    #(CLK_PEROID * 2);
    assert (dut.axi_interconnect.o_subordinator_axi_example_iface_wvalid == 1);
    assert (wvalid_value == dut.axi_interconnect.o_subordinator_axi_example_iface_wdata);
  end



endmodule
