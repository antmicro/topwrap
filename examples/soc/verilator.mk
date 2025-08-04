# Copyright 2024 Antmicro
# SPDX-License-Identifier: Apache-2.0

VERILATOR = verilator

PROJECT_DIR ?= .

VERILOG_SRC = $(PROJECT_DIR)/build/simple_soc.sv $(PROJECT_DIR)/sources/mem.v $(PROJECT_DIR)/sources/VexRiscv.v $(PROJECT_DIR)/sources/wb_uart.v $(PROJECT_DIR)/sources/crg.v
CPP_SRC = $(PROJECT_DIR)/sim.cpp

VERILATOR_FLAGS += -cc --exe -x-assign fast -Wall --trace --assert --coverage -Wno-COMBDLY -Wno-CASEINCOMPLETE -Wno-TIMESCALEMOD -Wno-UNUSEDSIGNAL -Wno-WIDTH -Wno-PINMISSING -Wno-DECLFILENAME -Wno-INITIALDLY -Wno-fatal --build --build-jobs 0 --top-module simple_soc --Mdir obj_dir
VERILATOR_INPUT = $(VERILOG_SRC) $(CPP_SRC)

$(BUILD_DIR)/obj_dir/Vtop: $(VERILOG_SRC)
	$(VERILATOR) $(VERILATOR_FLAGS) $(VERILATOR_INPUT)
