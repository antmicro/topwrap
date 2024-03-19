# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

# -------------------------------------
# Project
# -------------------------------------
DESIGN		:=	project.yml
SOURCE_DIR 	:=	sources
BUILD_DIR 	:=	build

SOURCE_FILES := \
	${SOURCE_DIR}/ibuf.v

# -------------------------------------
# Topwrap
# -------------------------------------
generate: copy_sources
	topwrap build --design ${DESIGN} --sources ${SOURCE_DIR}

# -------------------------------------
# Utilities
# -------------------------------------
copy_sources:
	mkdir -p ${BUILD_DIR}/sources
	cp -rf ${SOURCE_DIR}/* ${BUILD_DIR}/sources/

clean:
	rm -f sources/*.json gen_*.yml gen_*.yaml
	rm -rf ${BUILD_DIR}/*

.PHONY: setup clean generate copy_sources all
