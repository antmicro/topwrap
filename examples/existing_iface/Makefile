REPO_NAME = existing_iface_repo
JSONS = kpm_spec.json kpm_dataflow.json
IPCORE_SOURCES = sources/manager.sv sources/subordinator.sv sources/axi4lite.sv

generate: $(BUILD_DIR)/existing_iface_example.sv

repo: $(REPO_NAME)

build:
	mkdir build

$(REPO_NAME): $(IPCORE_SOURCES)
	topwrap repo init $(REPO_NAME) $(REPO_NAME)
	topwrap repo parse $(REPO_NAME) $(IPCORE_SOURCES) --frontend systemverilog -e skip

$(BUILD_DIR)/existing_iface_example.sv: design.yaml $(REPO_NAME) | build
	topwrap build -b build --design $<

$(JSONS): design.yaml $(REPO_NAME)
	topwrap --repo ${REPO_NAME} specification -d $<
	topwrap --repo ${REPO_NAME} dataflow -d $<

.PHONY: generate repo
