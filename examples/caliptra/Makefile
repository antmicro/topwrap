# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

CALIPTRA_RTL_SHA = 07b75fe4130b9d62d2eb9425499f09b2a38ead98

Caliptra:
	git clone https://github.com/chipsalliance/caliptra-rtl.git Caliptra
	git -C Caliptra checkout $(CALIPTRA_RTL_SHA)

clean:
	rm -rf Caliptra

.PHONY: clean
