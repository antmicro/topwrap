# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

BUILD_DIR = build

all: $(BUILD_DIR)

$(BUILD_DIR): project.yaml
	topwrap generate $< --specification --diagram

gui: project.yaml
	topwrap gui -d $<

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean gui
