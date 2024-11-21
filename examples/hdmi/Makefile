# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json

all: zvb

build:
	mkdir build

parse:
	topwrap parse --iface-deduce sources/clock_crossing.v sources/ps7.v

generate: build
	topwrap build --design project.yaml --fuse --sources sources

copy_sources: build
	cp -rf sources/ build/
	cp -rf ipcores/* build/

fusesoc_init:
	fusesoc library add fusesoc_cores https://github.com/fusesoc/fusesoc-cores

snickerdoodle: generate copy_sources fusesoc_init
	cp constr/snickerdoodle.xdc build/
	fusesoc --cores-root build run --build --target snickerdoodle project_1

zvb: generate copy_sources fusesoc_init
	cp constr/zynq_video_board.xdc build/
	fusesoc --cores-root build run --build --target zynq_video_board project_1

clean:
	rm -rf fusesoc.conf fusesoc_libraries
	rm -f sources/*.json
	rm -rf build/*
	rm -f cdc_flag.yaml ps7_inst.yaml

deps:
	pip install -r requirements.txt

ci: deps generate

$(JSONS):
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

.PHONY: clean copy_sources fusesoc_init generate copy_sources snickerdoodle zvb deps ci all
