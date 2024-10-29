# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json
SOURCE_DIR := verilogs
IPCORES_DIR := ipcores
SOURCE_FILES := \
	${SOURCE_DIR}/simple_core_1.v \
	${SOURCE_DIR}/simple_core_2.v


all: $(JSONS)

$(JSONS): parse
	topwrap specification ${IPCORES_DIR}/*.yaml
	topwrap dataflow -d project.yaml ${IPCORES_DIR}/*.yaml

parse: clean setup
	topwrap parse --iface-deduce ${SOURCE_FILES} --dest-dir=${IPCORES_DIR}/

clean:
	rm -f $(JSONS)
	rm -rf ${IPCORES_DIR}/*

setup:
	mkdir -p ${IPCORES_DIR}

.PHONY: all clean parse setup
