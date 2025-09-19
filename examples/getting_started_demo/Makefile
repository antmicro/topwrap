# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json
SOURCE_DIR := verilogs
REPO_NAME := my_repo

all: $(JSONS)

$(JSONS): parse
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

parse:
	topwrap repo init ${REPO_NAME} ${REPO_NAME}
	topwrap repo parse ${REPO_NAME} ${SOURCE_DIR}

clean:
	rm -f $(JSONS)
	rm -rf ${REPO_NAME}

.PHONY: all clean parse
