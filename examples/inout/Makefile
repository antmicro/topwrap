# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

# -------------------------------------
# Project
# -------------------------------------
DESIGN		=	project.yml
SOURCE_DIR 	=	sources
BUILD_DIR 	=	build
IPCORES_DIR	=	ipcores

SOURCE_FILES = \
	${SOURCE_DIR}/ibuf.v \
	${SOURCE_DIR}/obuf.v \
	${SOURCE_DIR}/iobuf.v

# -------------------------------------
# Toolchain
# -------------------------------------
PART	=	xc7z010clg400-1

TOOL	?=	symbiflow
# TOOL	?=	vivado

TARGET 	?= 	zynq
# -------------------------------------
# Topwrap
# -------------------------------------
all: bit

parse: clean setup
	fpga_topwrap parse --iface-deduce ${SOURCE_FILES} --dest-dir=${IPCORES_DIR}/

generate: parse copy_sources
	fpga_topwrap build --design ${DESIGN} --part ${PART} --sources ${SOURCE_DIR}

# -------------------------------------
# Bitstream generation
# -------------------------------------
bit: generate
	fusesoc --cores-root build run --tool=${TOOL} --build --target ${TARGET} project_1

# -------------------------------------
# Utilities
# -------------------------------------
setup:
	mkdir -p ${BUILD_DIR} ${IPCORES_DIR}

copy_sources:
	mkdir -p build/sources
	cp -rf ${SOURCE_DIR}/* ${BUILD_DIR}/sources/

clean:
	rm -f sources/*.json gen_*.yml gen_*.yaml
	rm -rf ${BUILD_DIR}/* ${IPCORES_DIR}/*

.PHONY: setup clean copy_sources generate copy_sources bit

