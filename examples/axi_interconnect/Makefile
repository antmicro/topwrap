# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

IPCORE_SOURCES = sources/manager_axi.v sources/subordinator_axi.v
REPO_NAME = axi_example_repo
JSONS = kpm_spec.json kpm_dataflow.json

VERILATOR = verilator

PROJECT_DIR ?= .
BUILD_DIR = $(PROJECT_DIR)/build
SCRIPTS_DIR = $(PROJECT_DIR)/scripts

VERILATOR_SKIP_WARNINGS := -Wno-TIMESCALEMOD -Wno-SELRANGE \
	-Wno-CASEINCOMPLETE -Wno-INITIALDLY -Wno-WIDTH -Wno-UNOPTFLAT -Wno-REDEFMACRO \
	-Wno-LATCH -Wno-MULTIDRIVEN -Wno-UNSIGNED -Wno-CMPCONST -Wno-UNUSEDPARAM -Wno-GENUNNAMED \
	-Wno-PINCONNECTEMPTY

FLIST_FILE_SOURCES = $(BUILD_DIR)/axi.f
FLIST_FILE_INCLUDES = $(BUILD_DIR)/axi_includes.f

FLIST_SOURCES=$(strip $(file < $(FLIST_FILE_SOURCES)))
FLIST_INCLUDES=$(strip $(file < $(FLIST_FILE_INCLUDES)))

VERILOG_SRC = $(FLIST_SOURCES) $(BUILD_DIR)/axi_interconnect_example.sv $(PROJECT_DIR)/sources/manager_axi.v $(PROJECT_DIR)/sources/subordinator_axi.v $(PROJECT_DIR)/testbench.sv

INCLUDE_FILES = $(FLIST_INCLUDES)

VERILATOR_FLAGS += -cc --binary --sv -x-assign fast -Wall --trace --assert -Wno-COMBDLY -Wno-CASEINCOMPLETE -Wno-TIMESCALEMOD -Wno-UNUSEDSIGNAL -Wno-WIDTH -Wno-PINMISSING -Wno-DECLFILENAME -Wno-INITIALDLY -Wno-fatal --build --build-jobs 0 --Mdir $(BUILD_DIR)/obj_dir $(VERILATOR_SKIP_WARNINGS) --top-module tb --timing

$(BUILD_DIR)/obj_dir/Vtb: $(VERILOG_SRC) $(FLIST_FILE_SOURCES)
	$(VERILATOR) $(addprefix -I,$(INCLUDE_FILES)) $(VERILOG_SRC) $(VERILATOR_FLAGS)

build:
	mkdir build

$(REPO_NAME): $(IPCORE_SOURCES)
	topwrap repo init $(REPO_NAME) $(REPO_NAME)
	topwrap repo parse $(REPO_NAME) $(IPCORE_SOURCES) -i

$(FLIST_FILE_SOURCES) $(FLIST_FILE_INCLUDES): $(SCRIPTS_DIR)/gen_flist.py | build
	python3 $< $(FLIST_FILE_SOURCES) $(FLIST_FILE_INCLUDES)

$(BUILD_DIR)/axi_interconnect_example.sv: design.yaml $(FLIST_FILE_SOURCES) $(IPCORE_YAMLS) $(REPO_NAME) | build
	topwrap build -b build --design $<

$(JSONS): $(REPO_NAME)
	topwrap specification -d design.yaml
	topwrap dataflow -d design.yaml

repo: $(REPO_NAME)

generate: $(BUILD_DIR)/axi_interconnect_example.sv

build-sim: $(BUILD_DIR)/axi_interconnect_example.sv $(BUILD_DIR)/obj_dir/Vtop

test:
	@echo $(INCLUDE_FILES)

wave.vcd: $(BUILD_DIR)/obj_dir/Vtb
	$(BUILD_DIR)/obj_dir/Vtb

sim: wave.vcd

clean:
	-rm -rf ipcores
	-rm -rf build
	-rm -rf obj_dir
	-rm -rf $(REPO_NAME)
	-rm wave.vcd
	-rm $(JSONS)

deps:
	pip install '../../.[parse]'

ci: deps generate

.PHONY: all generate build-sim sim clean deps ci generate repo
