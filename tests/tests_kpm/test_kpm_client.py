import logging
from pathlib import Path
from typing import Dict

import pytest
from deepdiff import DeepDiff
from pipeline_manager_backend_communication.misc_structures import MessageType
from pipeline_manager_backend_communication.utils import convert_message_to_string

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from topwrap.kpm_common import RPCparams
from topwrap.kpm_dataflow_parser import kpm_dataflow_to_design
from topwrap.kpm_topwrap_client import RPCMethods
from topwrap.util import JsonType
from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


class TestClient:
    @pytest.fixture
    def default_rpc_params(self):
        return RPCparams("127.0.0.1", 9000, ipcore_yamls_to_kpm_spec([]), Path("build"), None)

    def test_specification(
        self, all_specification_files, all_designs, default_rpc_params: RPCparams
    ):
        # Testing all cores
        for test_name, spec in all_specification_files.items():
            default_rpc_params.specification = ipcore_yamls_to_kpm_spec([], all_designs[test_name])
            specification_from_kpm = RPCMethods(default_rpc_params).specification_get()
            assert specification_from_kpm["type"] == MessageType.OK.value, (
                f"Test for {test_name} didn't return Message OK"
            )

            spec_differences = DeepDiff(
                specification_from_kpm.get("content"),
                spec,
                ignore_order=True,
                ignore_type_in_groups=[(list, tuple)],
            )
            assert spec_differences == {}, (
                f"Test {test_name} differs from original specification. Diff: {spec_differences}"
            )

    def test_dataflow_validation(
        self, all_dataflow_files, all_designs, default_rpc_params: RPCparams
    ):
        for test_name, dataflow_json in all_dataflow_files.items():
            default_rpc_params.specification = ipcore_yamls_to_kpm_spec([], all_designs[test_name])
            response_message = RPCMethods(default_rpc_params).dataflow_validate(dataflow_json)
            assert response_message["type"] != MessageType.ERROR.value, (
                f"Dataflow validation returned errors {response_message.get('content')} for test {test_name}"
            )
            if response_message["type"] == MessageType.WARNING.value:
                logging.warning(
                    f"Dataflow {test_name} has warnings {response_message.get('content')}"
                )

    def test_dataflow_run(self, all_dataflow_files, all_designs, default_rpc_params: RPCparams):
        for test_name, dataflow_json in all_dataflow_files.items():
            default_rpc_params.specification = ipcore_yamls_to_kpm_spec([], all_designs[test_name])
            response_message = RPCMethods(default_rpc_params).dataflow_run(dataflow_json)
            assert response_message["type"] == MessageType.OK.value, (
                f"Dataflow run returned {response_message} for test {test_name}"
            )

    def test_dataflow_export(self, all_dataflow_files, all_designs, default_rpc_params: RPCparams):
        for test_name, dataflow_json in all_dataflow_files.items():
            default_rpc_params.specification = ipcore_yamls_to_kpm_spec([], all_designs[test_name])
            response_message = RPCMethods(default_rpc_params).dataflow_export(dataflow_json)

            response_design_dict = DesignDescription.from_yaml(
                convert_message_to_string(response_message["content"], True, "application/x-yaml")
            )
            # Dump design and load back with yaml to avoid errors with different types like tuple vs list
            # design_loaded_yaml = yaml.safe_load(all_designs[test_name].to_yaml())
            design_diff = DeepDiff(
                all_designs[test_name].to_dict(), response_design_dict.to_dict(), ignore_order=True
            )
            assert design_diff == {}, (
                f"Dataflow export returned different encoded file for test {test_name}"
            )

    def test_dataflow_import(
        self, all_designs, all_encoded_design_files, default_rpc_params: RPCparams
    ):
        for test_name, design in all_designs.items():
            default_rpc_params.specification = ipcore_yamls_to_kpm_spec([], design)
            response_message = RPCMethods(default_rpc_params).dataflow_import(
                all_encoded_design_files[test_name], "application/x-yaml", True
            )

            # Checks if imported dataflow is correct are done in "test_kpm_import.py"
            assert response_message["type"] == MessageType.OK.value, (
                f"Dataflow import returned {response_message['type']} for test {test_name}"
            )

    def test_import_export_non_destructivity(
        self,
        all_designs: Dict[str, DesignDescription],
        all_specification_files: Dict[str, JsonType],
    ):
        for test_name, spec in all_specification_files.items():
            imported = all_designs[test_name]
            dataflow = kpm_dataflow_from_design_descr(imported, spec)
            exported = kpm_dataflow_to_design(dataflow, spec)

            assert (
                DeepDiff(
                    imported.to_dict(),
                    exported.to_dict(),
                    # permit arbitrary reordering of external ports
                    ignore_order_func=lambda lvl: "external" in lvl.path(),
                )
                == {}
            ), f'Exported design file for test "{test_name}" differs from the imported one'
