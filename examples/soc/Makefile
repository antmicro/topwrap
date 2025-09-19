# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

IPCORE_SOURCES = sources/mem.v sources/VexRiscv.v sources/crg.v sources/wb_uart.v
JSONS = kpm_spec.json kpm_dataflow.json
REPO_NAME := my_repo

all: upload

build:
	mkdir build

ipcores:
	mkdir ipcores

$(REPO_NAME): $(IPCORE_SOURCES)
	topwrap repo init ${REPO_NAME} ${REPO_NAME}
# FIXME: this will be broken until iface deduction returns
	topwrap repo parse ${REPO_NAME} ${IPCORE_SOURCES}

build/simple_soc.sv: project.yaml $(REPO_NAME) | build
	topwrap --repo ${REPO_NAME} build -b build --design $< --fuse --sources sources

build/helloworld.bin: helloworld.asm | build
	riscv64-unknown-elf-as -mabi=ilp32 -march=rv32i -o $@ $<

build/bios.bin: build/helloworld.bin | build
	riscv64-unknown-elf-objcopy -O binary $< $@

build/bios.init: build/bios.bin | build
	hexdump -v -e '1/4 "%08X\n"' $< > $@

build/simple_soc.bit: simple_soc.tcl build/bios.init $(IPCORE_SOURCES) build/simple_soc.sv | build
	vivado -mode batch -source $<

$(JSONS): $(REPO_NAME)
	touch $@
# FIXME: When interface deduction works again and interfaces from this
# 			example can get deduced
# 	topwrap --repo ${REPO_NAME} specification -d project.yaml
# 	topwrap --repo ${REPO_NAME} dataflow -d project.yaml

generate: build/simple_soc.sv

build-sim: build/simple_soc.sv
	$(MAKE) -f verilator.mk

sim: build-sim build/bios.init obj_dir/Vsimple_soc
	obj_dir/Vsimple_soc
	vcd2fst build/dump.vcd build/dump.fst

bitstream: build/simple_soc.bit

upload: build/simple_soc.bit
	openFPGALoader --board antmicro_lpddr4_tester $<

clean:
	rm -rf ipcores
	rm -rf build
	rm -rf obj_dir
	# vivado data
	rm -rf .Xil simple_soc.hw simple_soc.cache simple_soc.ip_user_files simple_soc.xpr
	rm -f vivado* usage_statistics_webtalk*
	rm -rf $(REPO_NAME)
	rm -f $(JSONS)

deps:
	pip install '../../.[parse]'

ci: deps generate

.PHONY: all generate build-sim sim bitstream upload clean deps ci generate
