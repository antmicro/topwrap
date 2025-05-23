# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

# -------------------------------------
# Project
# -------------------------------------
DESIGN		:=	project.yaml
SOURCE_DIR 	:=	sources
BUILD_DIR 	:=	build
IPCORES_DIR	:=	ipcores

SOURCE_FILES := \
	${SOURCE_DIR}/ibuf.v \
	${SOURCE_DIR}/obuf.v \
	${SOURCE_DIR}/iobuf.v

JSONS = kpm_spec.json kpm_dataflow.json

# -------------------------------------
# Toolchain
# -------------------------------------
PART	:=	xc7z010clg400-1

TOOL	:=	symbiflow
# TOOL	:=	vivado

TARGET  := 	zynq
# -------------------------------------
# Topwrap
# -------------------------------------
all: bit

parse: clean setup
	topwrap parse --iface-deduce ${SOURCE_FILES} --dest-dir=${IPCORES_DIR}/

generate: parse copy_sources
	topwrap build --design ${DESIGN} --fuse --part ${PART} --sources ${SOURCE_DIR}

# -------------------------------------
# Bitstream generation
# -------------------------------------
bit: generate fusesoc_init
	fusesoc --cores-root build run --tool=${TOOL} --build --target ${TARGET} project_1

# -------------------------------------
# Utilities
# -------------------------------------
fusesoc_init:
	fusesoc library add fusesoc_cores https://github.com/fusesoc/fusesoc-cores

setup:
	mkdir -p ${BUILD_DIR} ${IPCORES_DIR}

copy_sources:
	mkdir -p ${BUILD_DIR}/sources
	cp -rf ${SOURCE_DIR}/* ${BUILD_DIR}/sources/

clean:
	rm -rf fusesoc.conf fusesoc_libraries
	rm -f sources/*.json
	rm -rf ${BUILD_DIR}/* ${IPCORES_DIR}/*

deps:
	pip install -r requirements.txt

ci: deps generate

$(JSONS): parse
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

.PHONY: setup clean fusesoc_init generate copy_sources bit parse deps ci all
