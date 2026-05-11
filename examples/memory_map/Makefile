# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

IPCORE_SOURCES = sources/mem.v sources/VexRiscv.v sources/crg.v sources/wb_uart.v
JSONS = kpm_spec.json kpm_dataflow.json
REPO_NAME := my_repo

all: upload

build:
	mkdir build

$(REPO_NAME): $(IPCORE_SOURCES)
	topwrap repo init ${REPO_NAME} ${REPO_NAME}
	topwrap repo parse ${REPO_NAME} ${IPCORE_SOURCES} --inference

build/simple_soc.sv: project.yaml $(REPO_NAME) | build
	topwrap --repo ${REPO_NAME} build -b build --design $< --fuse

$(JSONS): $(REPO_NAME)
	topwrap --repo ${REPO_NAME} specification -d project.yaml
	topwrap --repo ${REPO_NAME} dataflow -d project.yaml

generate: build/simple_soc.sv

clean:
	rm -rf build
	rm -f $(JSONS)

.PHONY: all generate clean
