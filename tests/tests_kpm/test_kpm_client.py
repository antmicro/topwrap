import logging
from pathlib import Path
from typing import Dict

import pytest
from deepdiff import DeepDiff
from pipeline_manager_backend_communication.misc_structures import MessageType

from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.kpm_common import RPCparams
from topwrap.kpm_topwrap_client import RPCMethods
from topwrap.util import JsonType


class TestClient:
    @pytest.fixture
    def default_rpc_params(self):
        return RPCparams(
            "127.0.0.1",
            9000,
            KpmSpecificationBackend.default().build(),
            Path("build"),
            None,
            [],
            [],
        )

    def test_specification(
        self,
        all_design_specifications: Dict[str, JsonType],
        all_specification_files: Dict[str, JsonType],
        default_rpc_params: RPCparams,
    ):
        # Testing all cores
        for test_name, spec in all_design_specifications.items():
            default_rpc_params.specification = spec
            specification_from_kpm = RPCMethods(default_rpc_params).specification_get()
            assert specification_from_kpm["type"] == MessageType.OK.value, (
                f"Test for {test_name} didn't return Message OK"
            )

            spec_differences = DeepDiff(
                specification_from_kpm.get("content"),
                all_specification_files[test_name],
                ignore_order=True,
                ignore_type_in_groups=[(list, tuple)],
                exclude_paths=["root['version']", "root['metadata']"],
            )
            assert spec_differences == {}, (
                f"Test {test_name} differs from original specification. Diff: {spec_differences}"
            )

    def test_dataflow_validation(
        self,
        all_dataflow_files: Dict[str, JsonType],
        all_design_specifications: Dict[str, JsonType],
        default_rpc_params: RPCparams,
    ):
        for test_name, dataflow_json in all_dataflow_files.items():
            default_rpc_params.specification = all_design_specifications[test_name]
            response_message = RPCMethods(default_rpc_params).dataflow_validate(dataflow_json)
            assert response_message["type"] != MessageType.ERROR.value, (
                f"Dataflow validation returned errors {response_message.get('content')} for"
                f" test {test_name}"
            )
            if response_message["type"] == MessageType.WARNING.value:
                logging.warning(
                    f"Dataflow {test_name} has warnings {response_message.get('content')}"
                )

    def test_dataflow_run(
        self,
        all_dataflow_files: Dict[str, JsonType],
        all_design_specifications: Dict[str, JsonType],
        default_rpc_params: RPCparams,
    ):
        for test_name, dataflow_json in all_dataflow_files.items():
            default_rpc_params.specification = all_design_specifications[test_name]
            response_message = RPCMethods(default_rpc_params).dataflow_run(dataflow_json)
            assert response_message["type"] == MessageType.OK.value, (
                f"Dataflow run returned {response_message} for test {test_name}"
            )

    def test_dataflow_import(
        self,
        test_dirs: Dict[str, Path],
        all_design_specifications: Dict[str, JsonType],
        all_encoded_design_files: Dict[str, str],
        default_rpc_params: RPCparams,
        monkeypatch: pytest.MonkeyPatch,
    ):
        for test_name, spec in all_design_specifications.items():
            # Change directory so we're able to find the repo/ subdirectory for the tests.
            with monkeypatch.context() as m:
                test_dir = test_dirs[test_name]
                m.chdir(
                    Path("examples") / test_name if test_dir.parts[-2] == "examples" else test_dir
                )

                default_rpc_params.specification = spec
                response_message = RPCMethods(default_rpc_params).dataflow_import(
                    all_encoded_design_files[test_name], "application/x-yaml", True
                )

                assert response_message["type"] == MessageType.OK.value, (
                    f"Dataflow import returned {response_message['type']} for test {test_name}"
                )
