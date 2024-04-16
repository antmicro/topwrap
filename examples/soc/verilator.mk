# Copyright 2024 Antmicro
# SPDX-License-Identifier: Apache-2.0

VERILATOR = verilator

VERILOG_SRC = build/simple_soc.v sources/mem.v sources/VexRiscv.v sources/wb_uart.v sources/crg.v sources/wb_interconnect.v
CPP_SRC = sim.cpp

VERILATOR_FLAGS += -cc --exe -x-assign fast -Wall --trace --assert --coverage -Wno-COMBDLY -Wno-CASEINCOMPLETE -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC -Wno-TIMESCALEMOD -Wno-INITIALDLY -Wno-fatal --build --build-jobs 0 --top-module simple_soc --Mdir obj_dir
VERILATOR_INPUT = $(VERILOG_SRC) $(CPP_SRC)

$(BUILD_DIR)/obj_dir/Vtop: $(VERILOG_SRC)
	$(VERILATOR) $(VERILATOR_FLAGS) $(VERILATOR_INPUT)
