# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

################################################################################
# IO constraints
################################################################################
# clk100:0
set_property LOC L19 [get_ports {clk100}]
set_property IOSTANDARD LVCMOS33 [get_ports {clk100}]

# serial:1.tx
set_property LOC AA20 [get_ports {serial_tx}]
set_property IOSTANDARD LVCMOS33 [get_ports {serial_tx}]

# serial:1.rx
set_property LOC AB20 [get_ports {serial_rx}]
set_property IOSTANDARD LVCMOS33 [get_ports {serial_rx}]

###############################################################################
# Clock constraints
################################################################################
create_clock -name clk100 -period 10.0 [get_ports clk100]

################################################################################
# False path constraints
################################################################################
set_false_path -quiet -to [get_cells -hierarchical -filter { mr_ff == TRUE }]

set_false_path -quiet -to [get_pins -filter {REF_PIN_NAME == PRE} -of_objects [get_cells -hierarchical -filter {ars_ff1 == TRUE || ars_ff2 == TRUE}]]

set_max_delay 2 -quiet -from [get_pins -filter {REF_PIN_NAME == C} -of_objects [get_cells -hierarchical -filter {ars_ff1 == TRUE}]] -to [get_pins -filter {REF_PIN_NAME == D} -of_objects [get_cells -hierarchical -filter {ars_ff2 == TRUE}]]

set_max_delay -quiet -through [get_pins -filter {REF_PIN_NAME == Q} -of_objects [get_cells -hierarchical -filter {slow_ff == TRUE}]] 250

set_max_delay -quiet -to [get_pins -filter {REF_PIN_NAME == D} -of_objects [get_cells -hierarchical -filter {slow_in == TRUE}]] 250
