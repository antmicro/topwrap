import logging

import pytest
from deepdiff import DeepDiff
from pipeline_manager_backend_communication.misc_structures import MessageType

from topwrap.kpm_common import RPCparams
from topwrap.kpm_topwrap_client import RPCMethods


class TestClient:
    @pytest.fixture
    def default_rpc_params(self):
        return RPCparams("127.0.0.1", 9000, [], "build", "")

    def test_specification(self, all_yaml_files, all_specification_files, default_rpc_params):
        # Testing all cores
        for (test_name, ip_core_yamls), spec_json in zip(
            all_yaml_files.items(), all_specification_files.values()
        ):
            default_rpc_params.yamlfiles = ip_core_yamls
            specification_from_kpm = RPCMethods(default_rpc_params).specification_get()
            assert (
                specification_from_kpm["type"] == MessageType.OK.value
            ), f"Test for {test_name} didn't return Message OK"

            spec_differences = DeepDiff(
                specification_from_kpm["content"],
                spec_json,
                ignore_order=True,
            )
            assert (
                spec_differences == {}
            ), f"Test {test_name} differs from original specification. Diff: {spec_differences}"

    def test_dataflow_validation(self, all_yaml_files, all_dataflow_files, default_rpc_params):
        for (test_name, ip_core_yamls), dataflow_json in zip(
            all_yaml_files.items(), all_dataflow_files.values()
        ):
            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_validate(dataflow_json)
            assert (
                response_message["type"] != MessageType.ERROR.value
            ), f"Dataflow validation returned errors {response_message['content']} for test {test_name}"
            if response_message["type"] == MessageType.WARNING.value:
                logging.warning(f"Dataflow {test_name} has warnings {response_message['content']}")

    def test_dataflow_run(self, all_yaml_files, all_dataflow_files, default_rpc_params):
        for (test_name, ip_core_yamls), dataflow_json in zip(
            all_yaml_files.items(), all_dataflow_files.values()
        ):
            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_run(dataflow_json)
            assert response_message == {
                "type": MessageType.OK.value,
                "content": "Build succeeded",
            }, f"Dataflow run returned {response_message} for test {test_name}"

    def test_dataflow_export(
        self, all_yaml_files, all_dataflow_files, all_encoded_design_files, default_rpc_params
    ):
        for (test_name, ip_core_yamls), dataflow_json, encoded_design in zip(
            all_yaml_files.items(), all_dataflow_files.values(), all_encoded_design_files.values()
        ):
            default_rpc_params.yamlfiles = ip_core_yamls

            response_message = RPCMethods(default_rpc_params).dataflow_export(dataflow_json)
            assert (
                response_message["content"] == encoded_design
            ), f"Dataflow export returned different encoded file for test {test_name}"

    def test_dataflow_import(self, all_yaml_files, all_encoded_design_files, default_rpc_params):
        for (test_name, ip_core_yamls), encoded_dataflow in zip(
            all_yaml_files.items(), all_encoded_design_files.values()
        ):
            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_import(
                encoded_dataflow, "application/x-yaml", True
            )

            # Checks if imported dataflow is correct are done in "test_kpm_import.py"
            assert (
                response_message["type"] == MessageType.OK.value
            ), f"Dataflow import returned {response_message['type']} for test {test_name}"
