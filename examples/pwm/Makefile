# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json

all: zvb

build:
	mkdir build

parse:
	topwrap parse --iface-deduce sources/litex_pwm.v sources/ps7.v

generate: build
	topwrap build --design project.yaml --fuse --sources sources --part xc7z010clg400-1

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
	rm -f sources/*.json
	rm -rf build/*
	rm -f litex_pwm.yaml ps7_inst.yaml

deps:
	pip install -r requirements.txt

ci: deps generate

$(JSONS):
	topwrap specification ipcores/*.yaml ../../topwrap/ips/axi/*.yaml
	topwrap dataflow -d project.yaml ipcores/*.yaml ../../topwrap/ips/axi/*.yaml

.PHONY: clean copy_sources fusesoc_init generate zvb deps ci all
