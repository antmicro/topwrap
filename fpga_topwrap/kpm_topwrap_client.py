# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import logging
from pipeline_manager_backend_communication. \
    communication_backend import CommunicationBackend
from pipeline_manager_backend_communication \
    .misc_structures import MessageType, Status


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
                client.send_message(
                    MessageType.ERROR,
                    "Not implemented".encode()
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
                client.send_message(
                    MessageType.ERROR,
                    "Not implemented".encode()
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
                client.send_message(
                    MessageType.ERROR,
                    "Not implemented".encode()
                )
