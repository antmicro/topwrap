# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

# -------------------------------------
# Project
# -------------------------------------
DESIGN		:=	project.yaml
SOURCE_DIR 	:=	sources
BUILD_DIR 	:=	build

SOURCE_FILES := \
	${SOURCE_DIR}/ibuf.v

JSONS = kpm_spec.json kpm_dataflow.json

# -------------------------------------
# Topwrap
# -------------------------------------
generate: copy_sources
	topwrap build --design ${DESIGN} --sources ${SOURCE_DIR}

$(JSONS):
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

# -------------------------------------
# Utilities
# -------------------------------------
copy_sources:
	mkdir -p ${BUILD_DIR}/sources
	cp -rf ${SOURCE_DIR}/* ${BUILD_DIR}/sources/

clean:
	rm -f sources/*.json
	rm -rf ${BUILD_DIR}/*

ci: generate

.PHONY: setup clean generate copy_sources ci all
