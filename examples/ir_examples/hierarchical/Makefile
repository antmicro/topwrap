# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json

all: $(JSONS)

$(JSONS):
	topwrap specification -d design.yaml
	topwrap dataflow -d design.yaml

clean:
	rm -f $(JSONS)
