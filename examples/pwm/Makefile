# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
all: generate copy_sources zvb

build:
	mkdir build

parse:
	fpga_topwrap parse --iface-deduce sources/litex_pwm.v sources/ps7.v

generate: build
	fpga_topwrap build --design project.yml --sources sources --part xc7z010clg400-1

copy_sources: build
	cp -rf sources/ build/
	cp -rf ipcores/* build/

zvb:
	fusesoc --cores-root build run --tool=symbiflow --build --target zynq project_1

zvb_vivado: generate copy_sources
	fusesoc --cores-root build run --tool=vivado --build --target zynq project_1

clean:
	rm -f sources/*.json gen_*.yml
	rm -rf build/*

.PHONY: clean copy_sources generate zvb
