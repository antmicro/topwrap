# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json
SOURCE_DIR := verilogs
REPO_NAME := my_repo

all: $(JSONS)

$(JSONS): package
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

package: cores/simple_core_1.yaml cores/simple_core_2.yaml

cores/%.yaml: cores/%.v
	topwrap package $< -o $@

clean:
	rm -f $(JSONS)
	rm -rf ${REPO_NAME}

.PHONY: all clean parse
