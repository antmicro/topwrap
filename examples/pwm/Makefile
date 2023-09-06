# Copyright (C) 2021-2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

all: zvb

build:
	mkdir build

parse:
	fpga_topwrap parse --iface-deduce sources/litex_pwm.v sources/ps7.v

generate: build
	fpga_topwrap build --design project.yml --sources sources --part xc7z010clg400-1

copy_sources: build
	cp -rf sources/ build/
	cp -rf ipcores/* build/

fusesoc_init:
	fusesoc library add fusesoc_cores https://github.com/fusesoc/fusesoc-cores

zvb: generate copy_sources fusesoc_init
	fusesoc --cores-root build run --tool=symbiflow --build --target zynq project_1

zvb_vivado: generate copy_sources fusesoc_init
	fusesoc --cores-root build run --tool=vivado --build --target zynq project_1

clean:
	rm -rf fusesoc.conf fusesoc_libraries
	rm -f sources/*.json gen_*.yml
	rm -rf build/*

.PHONY: clean copy_sources fusesoc_init generate zvb
