# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import logging
import os

import yaml
from pipeline_manager_backend_communication.communication_backend import (
    CommunicationBackend,
)
from pipeline_manager_backend_communication.misc_structures import MessageType, Status

from .design import build_design
from .design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from .kpm_dataflow_parser import kpm_dataflow_to_design
from .kpm_dataflow_validator import validate_kpm_design
from .yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


def _kpm_specification_handler(yamlfiles: list) -> str:
    """Return KPM specification containing info about IP cores.
    The specification is generated from given IP core description YAMLs.
    """
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return json.dumps(specification)


def _kpm_import_handler(data: bytes, yamlfiles: list) -> str:
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    dataflow = kpm_dataflow_from_design_descr(yaml.safe_load(data.decode()), specification)
    return json.dumps(dataflow)


def _ipcore_names_to_yamls_mapping(yamlfiles: list) -> dict:
    return {os.path.splitext(os.path.basename(yamlfile))[0]: yamlfile for yamlfile in yamlfiles}


def _design_from_kpm_data(data: bytes, yamlfiles: list) -> dict:
    json_data = json.loads(data.decode())
    ipcore_to_yamls = _ipcore_names_to_yamls_mapping(yamlfiles)
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return kpm_dataflow_to_design(json_data, ipcore_to_yamls, specification)


def _kpm_run_handler(data: bytes, yamlfiles: list) -> list:
    """Parse information about design from KPM dataflow format into Topwrap's
    internal representation and build the design.
    """
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    messages = validate_kpm_design(data, specification)
    if not messages["errors"]:
        design = _design_from_kpm_data(data, yamlfiles)
        build_design(design)
    return messages["errors"]


def _kpm_validate_handler(data: bytes, yamlfiles: list) -> dict:
    specification = ipcore_yamls_to_kpm_spec(yamlfiles)
    return validate_kpm_design(data, specification)


def _generate_design_filename() -> str:
    """Return a design description YAML file name where the design
    description will be written to.
    """
    timestamp = datetime.datetime.now()
    (year, month, day, hour, minute, second) = (
        str(timestamp.year),
        str(timestamp.month),
        str(timestamp.day),
        str(timestamp.hour),
        str(timestamp.minute),
        str(timestamp.second),
    )
    return "kpm_design_" + year + month + day + "_" + hour + minute + second + ".yaml"


def _kpm_export_handler(data: bytes, yamlfiles: list) -> str:
    """Save created dataflow into Topwrap's design description YAML.
    Return value is a file name where the design is saved - it is
    automatically generated based on current timestamp.
    """
    design_file = _generate_design_filename()
    design = _design_from_kpm_data(data, yamlfiles)

    with open(design_file, "w") as f:
        yaml.safe_dump(design, f, sort_keys=False)

    return os.path.abspath(design_file)


def kpm_run_client(host: str, port: int, yamlfiles: str):
    logging.basicConfig(level=logging.INFO)

    client = CommunicationBackend(host, port)
    client.initialize_client()

    while True:
        status, message = client.wait_for_message()

        if status == Status.DATA_READY:
            message_type, data = message

            if message_type == MessageType.SPECIFICATION:
                logging.info(f"Specification request received from {host}:{port}")
                format_spec = _kpm_specification_handler(yamlfiles)
                client.send_message(MessageType.OK, format_spec.encode())

            elif message_type == MessageType.RUN:
                logging.info(f"Dataflow run request received from {host}:{port}")
                errors = _kpm_run_handler(data, yamlfiles)
                if errors:
                    client.send_message(MessageType.ERROR, errors[0].encode())
                else:
                    client.send_message(MessageType.OK, "Build succeeded".encode())

            elif message_type == MessageType.VALIDATE:
                logging.info(f"Dataflow validation request received from {host}:{port}")
                messages = _kpm_validate_handler(data, yamlfiles)
                if messages["errors"]:
                    client.send_message(MessageType.ERROR, messages["errors"][0].encode())
                elif messages["warnings"]:
                    client.send_message(MessageType.OK, messages["warnings"][0].encode())
                else:
                    client.send_message(MessageType.OK, "Design is valid".encode())

            elif message_type == MessageType.EXPORT:
                logging.info(f"Dataflow export request received from {host}:{port}")
                design_file = _kpm_export_handler(data, yamlfiles)
                client.send_message(MessageType.OK, f"Design saved to {design_file}".encode())

            elif message_type == MessageType.IMPORT:
                logging.info(f"Dataflow import request received from {host}:{port}")
                dataflow = _kpm_import_handler(data, yamlfiles)
                client.send_message(MessageType.OK, dataflow.encode())
