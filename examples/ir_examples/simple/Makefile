# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json

all: $(JSONS)

$(JSONS):
	topwrap specification ips/*.yaml
	topwrap dataflow -d design.yaml ips/*.yaml

clean:
	rm -f $(JSONS)
