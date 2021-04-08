# Copyright (C) 2021  Antmicro
# SPDX-License-Identifier: Apache-2.0
echo "Prebuild script started."
# Get rid of $display, because Yosys raises error:
# System task `$display' called with invalid/unsupported format specifier
sed -i '/$display/d' ../src/verilog-axi_0/rtl/axi_interconnect.v
echo "Prebuild done."
