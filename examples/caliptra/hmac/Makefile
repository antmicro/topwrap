# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

JSONS = kpm_spec.json kpm_dataflow.json
CALIPTRA_RTL_SHA = 07b75fe4130b9d62d2eb9425499f09b2a38ead98

all: $(JSONS)

$(JSONS) &: kpm_build.py
	if [ ! -d "../Caliptra" ]; then \
		git clone https://github.com/chipsalliance/caliptra-rtl.git ../Caliptra; \
		git -C ../Caliptra checkout $(CALIPTRA_RTL_SHA); \
	fi
	python -m kpm_build

clean:
	rm -f $(JSONS)

.PHONY: all clean
