# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
all: zvb

build:
	mkdir build

parse:
	fpga_topwrap parse --iface-deduce sources/clock_crossing.v sources/ps7.v

generate: build
	fpga_topwrap build --design project.yml --sources sources

copy_sources: build
	cp -rf sources/ build/
	cp -rf ipcores/* build/

snickerdoodle: generate copy_sources
	cp constr/snickerdoodle.xdc build/
	fusesoc --cores-root build run --build --target snickerdoodle project_1

zvb: generate copy_sources
	cp constr/zynq_video_board.xdc build/
	fusesoc --cores-root build run --build --target zynq_video_board project_1

clean:
	rm -f sources/*.json gen_*.yml
	rm -rf build/*

.PHONY: clean copy_sources generate copy_sources snickerdoodle zvb
