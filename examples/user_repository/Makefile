# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json
REPO_NAME = repo


all: $(JSONS)

generate_ipxact: project.yaml $(REPO_NAME)
	topwrap ipxact_gen -d $<

$(JSONS):
	topwrap specification -d project.yaml
	topwrap dataflow -d project.yaml

clean:
	rm -f $(JSONS)

.PHONY: all clean
