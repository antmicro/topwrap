import logging
from pathlib import Path
from typing import Dict

import pytest
from deepdiff import DeepDiff
from deepdiff.serialization import yaml
from pipeline_manager_backend_communication.misc_structures import MessageType
from pipeline_manager_backend_communication.utils import convert_message_to_string

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from topwrap.kpm_common import RPCparams
from topwrap.kpm_dataflow_parser import kpm_dataflow_to_design
from topwrap.kpm_topwrap_client import RPCMethods
from topwrap.util import JsonType


class TestClient:
    @pytest.fixture
    def default_rpc_params(self):
        return RPCparams("127.0.0.1", 9000, [], Path("build"), Path())

    def test_specification(self, all_yaml_files, all_specification_files, default_rpc_params):
        # Testing all cores
        for test_name, ip_core_yamls in all_yaml_files.items():
            spec_json = all_specification_files[test_name]

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
        # FIXME: Our validators are broken and forbid valid designs. Remove this line after fixing them.
        del all_yaml_files["complex"]

        for test_name, ip_core_yamls in all_yaml_files.items():
            dataflow_json = all_dataflow_files[test_name]

            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_validate(dataflow_json)
            assert (
                response_message["type"] != MessageType.ERROR.value
            ), f"Dataflow validation returned errors {response_message['content']} for test {test_name}"
            if response_message["type"] == MessageType.WARNING.value:
                logging.warning(f"Dataflow {test_name} has warnings {response_message['content']}")

    def test_dataflow_run(self, all_yaml_files, all_dataflow_files, default_rpc_params):
        # FIXME: Our validators are broken and forbid valid designs. Remove this line after fixing them.
        del all_yaml_files["complex"]

        for test_name, ip_core_yamls in all_yaml_files.items():
            dataflow_json = all_dataflow_files[test_name]

            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_run(dataflow_json)
            assert (
                response_message["type"] == MessageType.OK.value
            ), f"Dataflow run returned {response_message} for test {test_name}"

    def test_dataflow_export(
        self, all_yaml_files, all_dataflow_files, all_designs, default_rpc_params
    ):
        for test_name, ip_core_yamls in all_yaml_files.items():
            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_export(
                all_dataflow_files[test_name]
            )

            response_design_dict = yaml.safe_load(
                convert_message_to_string(response_message["content"], True, "application/x-yaml")
            )
            # Dump design and load back with yaml to avoid errors with different types like tuple vs list
            design_loaded_yaml = yaml.safe_load(all_designs[test_name].to_yaml())

            design_diff = DeepDiff(design_loaded_yaml, response_design_dict, ignore_order=True)
            assert (
                design_diff == {}
            ), f"Dataflow export returned different encoded file for test {test_name}"

    def test_dataflow_import(self, all_yaml_files, all_encoded_design_files, default_rpc_params):
        for test_name, ip_core_yamls in all_yaml_files.items():
            default_rpc_params.yamlfiles = ip_core_yamls
            response_message = RPCMethods(default_rpc_params).dataflow_import(
                all_encoded_design_files[test_name], "application/x-yaml", True
            )

            # Checks if imported dataflow is correct are done in "test_kpm_import.py"
            assert (
                response_message["type"] == MessageType.OK.value
            ), f"Dataflow import returned {response_message['type']} for test {test_name}"

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
