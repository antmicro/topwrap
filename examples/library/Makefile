# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

BUILD_DIR = build

all: $(BUILD_DIR)

$(BUILD_DIR): project.yaml
	topwrap generate $< --specification --diagram

gui: project.yaml
	topwrap gui -d $<

# Regenerate the cores from the sources with topwrap package.
topwrap.yaml:
	topwrap library add example_cores ./cores

cores: cores/producer/module.yaml cores/consumer/module.yaml

cores/producer/module.yaml: cores/producer/producer.sv topwrap.yaml
	topwrap package $< --vlnv example.com:demo:producer:0.1 \
	  --inference --grouping-hint p=stream_out --lib -o $@

cores/consumer/module.yaml: cores/consumer/consumer.sv topwrap.yaml
	topwrap package $< --vlnv example.com:demo:consumer:0.1 \
	  --inference --grouping-hint c=stream_in --lib -o $@

cores/producer/producer.core: cores/producer/module.yaml
	@:

cores/consumer/consumer.core: cores/consumer/module.yaml
	@:

clean:
	rm -rf $(BUILD_DIR)

clean-cores:
	rm -f cores/producer/module.yaml cores/consumer/module.yaml
	rm -f cores/producer/producer.core cores/consumer/consumer.core
	rm -f topwrap.yaml

.PHONY: all clean gui cores clean-cores
