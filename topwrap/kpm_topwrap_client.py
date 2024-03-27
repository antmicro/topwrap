# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from base64 import b64encode
from datetime import datetime

import yaml
from pipeline_manager_backend_communication.communication_backend import (
    CommunicationBackend,
)
from pipeline_manager_backend_communication.misc_structures import MessageType
from pipeline_manager_backend_communication.utils import convert_message_to_string

from .design import build_design
from .design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from .kpm_dataflow_parser import kpm_dataflow_to_design
from .kpm_dataflow_validator import validate_kpm_design
from .yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


def _kpm_specification_handler(yamlfiles: list) -> str:
    """Return KPM specification containing info about IP cores.
    The specification is generated from given IP core description YAMLs.
    """
    return ipcore_yamls_to_kpm_spec(yamlfiles)


def _kpm_import_handler(data: bytes, yamlfiles: list) -> str:
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return kpm_dataflow_from_design_descr(yaml.safe_load(data), specification)


def _design_from_kpm_data(data: dict, yamlfiles: list) -> dict:
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return kpm_dataflow_to_design(data, specification)


def _kpm_run_handler(data: dict, yamlfiles: list, build_dir: str) -> list:
    """Parse information about design from KPM dataflow format into Topwrap's
    internal representation and build the design.
    """
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    messages = validate_kpm_design(data, specification)
    if not messages["errors"]:
        design = _design_from_kpm_data(data, yamlfiles)
        build_design(design, build_dir)
    return messages["errors"]


def _kpm_validate_handler(data: dict, yamlfiles: list) -> dict:
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return validate_kpm_design(data, specification)


def _generate_design_filename() -> str:
    """Return a design description YAML file name where the design
    description will be written to.
    """
    return datetime.now().strftime("kpm_design_%Y%m%d_%H%M%S.yaml")


def _kpm_export_handler(dataflow: dict, yamlfiles: list) -> str:
    """Convert created dataflow into Topwrap's design description YAML.

    :param dataflow: dataflow JSON from KPM
    :param yamlfiles: additional YAML files containing IP core descriptions

    :return: pair: converted YAML string, automatically generated filename
    with current timestamp
    """
    filename = _generate_design_filename()
    design = _design_from_kpm_data(dataflow, yamlfiles)
    return (yaml.safe_dump(design, sort_keys=False), filename)


async def kpm_run_client(host: str, port: int, yamlfiles: list, build_dir: str):
    class RPCMethods:
        def app_capabilities_get(self) -> dict:
            return {"stoppable_methods": ["dataflow_run"]}

        def specification_get(self) -> dict:
            logging.info(f"Specification get request from {host}:{port}")
            from .yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

            specification = ipcore_yamls_to_kpm_spec(yamlfiles)
            return {"type": MessageType.OK.value, "content": specification}

        def dataflow_validate(self, dataflow: dict) -> dict:
            logging.info(f"Dataflow validation request received from {host}:{port}")
            messages = _kpm_validate_handler(dataflow, yamlfiles)
            if messages["errors"]:
                # note: only the first error is sent to the KPM frontend
                return {"type": MessageType.ERROR.value, "content": messages["errors"][0]}
            elif messages["warnings"]:
                return {
                    "type": MessageType.WARNING.value,
                    "content": messages["warnings"][0],
                }
            else:
                return {"type": MessageType.OK.value, "content": "Design is valid"}

        def dataflow_run(self, dataflow: dict) -> dict:
            logging.info(f"Dataflow run request received from {host}:{port}")
            errors = _kpm_run_handler(dataflow, yamlfiles, build_dir)
            if errors:
                # note: only the first error is sent to the KPM frontend
                return {"type": MessageType.ERROR.value, "content": errors[0]}
            else:
                return {"type": MessageType.OK.value, "content": "Build succeeded"}

        def dataflow_stop(self, method: str) -> dict:
            logging.info(f"Dataflow stop request from {host}:{port}")
            return {"type": MessageType.OK.value}

        def dataflow_export(self, dataflow: dict, *args, **kwargs) -> dict:
            logging.info(f"Dataflow export request received from {host}:{port}")
            yaml_str, filename = _kpm_export_handler(dataflow, yamlfiles)
            # content sent to KPM frontend needs to be base64 encoded, but
            # b64encode expects a bytes-like object as an argument therefore
            # the string needs to be converted to bytes first and then converted
            # back to string because "content" field is expected to be a string
            yaml_b64encoded = b64encode(yaml_str.encode("utf-8")).decode("utf-8")
            return {"type": MessageType.OK.value, "content": yaml_b64encoded, "filename": filename}

        def dataflow_import(
            self, external_application_dataflow: str, mime: str, base64: bool
        ) -> dict:
            logging.info(f"Dataflow import request received from {host}:{port}")
            yaml_str = convert_message_to_string(external_application_dataflow, base64, mime)
            dataflow = _kpm_import_handler(yaml_str, yamlfiles)
            return {
                "type": MessageType.OK.value,
                "content": dataflow,
            }

    client = CommunicationBackend(host, port)
    logging.debug("Initializing RPC client")
    await client.initialize_client(RPCMethods())
    await client.start_json_rpc_client()
