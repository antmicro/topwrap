# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

# Create Project

create_project -force -name simple_soc -part xc7k70tfbg484-3
set_msg_config -id {Common 17-55} -new_severity {Warning}

# Add Sources

read_verilog {sources/crg.v}
read_verilog {sources/mem.v}
read_verilog {sources/VexRiscv.v}
read_verilog {sources/wb_interconnect.v}
read_verilog {sources/wb_uart.v}
read_verilog {build/simple_soc.v}

# Add constraints

read_xdc simple_soc.xdc
set_property PROCESSING_ORDER EARLY [get_files simple_soc.xdc]

# Synthesis

synth_design -directive default -top simple_soc -part xc7k70tfbg484-3

# Synthesis report

report_timing_summary -file build/top_timing_synth.rpt
report_utilization -hierarchical -file build/top_utilization_hierarchical_synth.rpt
report_utilization -file build/top_utilization_synth.rpt

# Optimize design

opt_design -directive default

# Placement

place_design -directive default

# Placement report

report_utilization -hierarchical -file build/top_utilization_hierarchical_place.rpt
report_utilization -file build/top_utilization_place.rpt
report_io -file build/top_io.rpt
report_control_sets -verbose -file build/top_control_sets.rpt
report_clock_utilization -file build/top_clock_utilization.rpt

# Routing

route_design -directive default
phys_opt_design -directive default
write_checkpoint -force build/top_route.dcp

# Routing report

report_timing_summary -no_header -no_detailed_paths
report_route_status -file build/top_route_status.rpt
report_drc -file build/top_drc.rpt
report_timing_summary -datasheet -max_paths 10 -file build/top_timing.rpt
report_power -file build/top_power.rpt
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]

# Bitstream generation

write_bitstream -force build/simple_soc.bit
write_cfgmem -force -format bin -interface spix4 -size 16 -loadbit "up 0x0 build/simple_soc.bit" -file build/simple_soc.bin

# End

quit
