# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import yaml
import json
import logging
from .yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from .design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from .kpm_dataflow_validator import validate_kpm_design
from pipeline_manager_backend_communication. \
    communication_backend import CommunicationBackend
from pipeline_manager_backend_communication \
    .misc_structures import MessageType, Status


def _kpm_specification_handler(yamlfiles: list) -> str:
    """ Return KPM specification containing info about IP cores.
    The specification is generated from given IP core description YAMLs.
    """
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return json.dumps(specification)


def _kpm_import_handler(data: bytes, yamlfiles: list) -> str:
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    dataflow = kpm_dataflow_from_design_descr(yaml.safe_load(data.decode()), specification)
    return json.dumps(dataflow)


def _kpm_validate_handler(data: bytes, yamlfiles: list) -> dict:
    return validate_kpm_design(data, yamlfiles)


def kpm_run_client(host: str, port: int, yamlfiles: str):
    logging.basicConfig(level=logging.INFO)

    client = CommunicationBackend(host, port)
    client.initialize_client()

    while True:
        status, message = client.wait_for_message()

        if status == Status.DATA_READY:
            message_type, data = message

            if message_type == MessageType.SPECIFICATION:
                logging.info(
                    f"Specification request received from {host}:{port}")
                format_spec = _kpm_specification_handler(yamlfiles)
                client.send_message(
                    MessageType.OK,
                    format_spec.encode()
                )

            elif message_type == MessageType.RUN:
                logging.info(
                    f"Dataflow run request received from {host}:{port}")
                client.send_message(
                    MessageType.ERROR,
                    "Not implemented".encode()
                )

            elif message_type == MessageType.VALIDATE:
                logging.info(
                    f"Dataflow validation request received from {host}:{port}")
                messages = _kpm_validate_handler(data, yamlfiles)
                if messages["errors"]:
                    client.send_message(
                        MessageType.ERROR,
                        messages["errors"][0].encode()
                    )
                elif messages["warnings"]:
                    client.send_message(
                        MessageType.OK,
                        messages["warnings"][0].encode()
                    )
                else:
                    client.send_message(
                        MessageType.OK,
                        "Design is valid".encode()
                    )

            elif message_type == MessageType.EXPORT:
                logging.info(
                    f"Dataflow export request received from {host}:{port}")
                client.send_message(
                    MessageType.ERROR,
                    "Not implemented".encode()
                )

            elif message_type == MessageType.IMPORT:
                logging.info(
                    f"Dataflow import request received from {host}:{port}")
                dataflow = _kpm_import_handler(data, yamlfiles)
                client.send_message(
                    MessageType.OK,
                    dataflow.encode()
                )
