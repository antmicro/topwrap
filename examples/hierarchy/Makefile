# Copyright (c) 2024-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json
REPO = my_repo
SOURCES = $(wildcard sources/*.v)

all: $(JSONS)

repo: $(REPO)

$(REPO): $(SOURCES)
	if [ ! -d "$@" ]; then \
		topwrap repo init $@ $@; \
		topwrap repo parse $@ $^; \
	fi
	touch $(REPO)

$(JSONS): $(REPO)
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

clean:
	rm -f $(JSONS)
	rm -rf $(REPO)

.PHONY: all clean repo
