# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json

all: $(JSONS)

$(JSONS) &: kpm_build.py
	python -m kpm_build

clean:
	rm -f $(JSONS)

.PHONY: all clean
