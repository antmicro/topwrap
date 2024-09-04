# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

IPCORE_SOURCES = sources/mem.v sources/VexRiscv.v sources/crg.v sources/wb_uart.v sources/wb_interconnect.v
IPCORE_YAMLS = ipcores/gen_mem.yaml ipcores/gen_VexRiscv.yaml ipcores/gen_crg.yaml ipcores/gen_wb_uart.yaml ipcores/gen_wb_interconnect.yaml
JSONS = kpm_spec.json kpm_dataflow.json

all: upload

build:
	mkdir build

ipcores:
	mkdir ipcores

$(IPCORE_YAMLS) &: $(IPCORE_SOURCES) | ipcores
	topwrap parse -d ipcores --iface-deduce $(IPCORE_SOURCES)

build/simple_soc.v: $(IPCORE_YAMLS) project.yaml | build
	topwrap build -b build --design project.yaml --sources sources

build/helloworld.bin: helloworld.asm | build
	riscv64-unknown-elf-as -mabi=ilp32 -march=rv32i -o $@ $<

build/bios.bin: build/helloworld.bin | build
	riscv64-unknown-elf-objcopy -O binary $< $@

build/bios.init: build/bios.bin | build
	hexdump -v -e '1/4 "%08X\n"' $< > $@

build/simple_soc.bit: build/bios.init simple_soc.tcl $(IPCORE_SOURCES) build/simple_soc.v | build
	vivado -mode batch -source simple_soc.tcl

$(JSONS): $(IPCORE_YAMLS)
	topwrap specification $(IPCORE_YAMLS)
	topwrap dataflow -d project.yaml $(IPCORE_YAMLS)


generate: build/simple_soc.v

build-sim: build/simple_soc.v
	$(MAKE) -fverilator.mk

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

deps:
	pip install '../../.[topwrap-parse]'

ci: deps generate

.PHONY: all generate build-sim sim bitstream upload clean deps ci
