# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
all: zvb

build:
	mkdir build

generate: build
	fpga_topwrap --design project.yml --sources sources --part xc7z010clg400-1

copy_sources: build
	cp -rf sources/ build/
	cp -rf ipcores/* build/

zvb: generate copy_sources
	fusesoc --cores-root build run --tool=symbiflow --build --target zynq project_1

zvb_vivado: generate copy_sources
	fusesoc --cores-root build run --tool=vivado --build --target zynq project_1

clean:
	rm -rf build/*

.PHONY: clean copy_sources generate zvb
