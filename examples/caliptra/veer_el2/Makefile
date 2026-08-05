# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json

all: $(JSONS)

../Caliptra:
	make -C .. Caliptra

$(JSONS) &: ../kpm_build.py ../Caliptra
	python ../kpm_build.py el2_veer

clean:
	rm -f $(JSONS)

.PHONY: all clean
