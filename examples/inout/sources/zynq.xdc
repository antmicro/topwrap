# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

set_property -dict { PACKAGE_PIN K17   IOSTANDARD LVCMOS33 } [get_ports { PORT_CLK }];
create_clock -add -name sys_clk_pin -period 8.00 -waveform {0 4} [get_ports { PORT_CLK }];

set_property -dict { PACKAGE_PIN G15   IOSTANDARD LVCMOS33 } [get_ports { PORT_RST }];
set_property -dict { PACKAGE_PIN P15   IOSTANDARD LVCMOS33 } [get_ports { PORT_IN }];

set_property -dict { PACKAGE_PIN M14   IOSTANDARD LVCMOS33 } [get_ports { PORT_OUT_0 }];
set_property -dict { PACKAGE_PIN M15   IOSTANDARD LVCMOS33 } [get_ports { PORT_OUT_1 }];
set_property -dict { PACKAGE_PIN G14   IOSTANDARD LVCMOS33 } [get_ports { PORT_OUT_2 }];

set_property -dict { PACKAGE_PIN D18   IOSTANDARD LVCMOS33 } [get_ports { PORT_IO }];
