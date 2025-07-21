# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import threading
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from pipeline_manager_backend_communication.communication_backend import (
    CommunicationBackend,
)
from pipeline_manager_backend_communication.misc_structures import MessageType
from pipeline_manager_backend_communication.utils import convert_message_to_string
from typing_extensions import NotRequired

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.dataflow import KpmDataflowBackend
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.fuse_helper import FuseSocBuilder
from topwrap.util import JsonType

from .kpm_common import RPCparams
from .kpm_dataflow_validator import DataflowValidator
from .util import read_json_file, save_file_to_json


class RPCEndpointReturnType(TypedDict):
    type: int
    content: NotRequired[Union[str, JsonType]]


class RPCExportEndpointReturnType(RPCEndpointReturnType):
    filename: str


class RPCMethods:
    def __init__(self, params: RPCparams, client: Optional[CommunicationBackend] = None):
        self.host = params.host
        self.port = params.port
        self.specification = params.specification
        self.build_dir = params.build_dir
        self.design = params.design
        self.client = client
        # Use the $XDG_DATA_HOME as a destination for saving the dataflow, which defaults to
        # ~/.local/share
        xdg_data_home_var = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
        self.default_save_file = xdg_data_home_var / "topwrap/dataflow_latest_save.json"
        self.initial_load = True

    def app_capabilities_get(self) -> Dict[Literal["stoppable_methods"], List[str]]:
        return {"stoppable_methods": ["dataflow_run"]}

    def specification_get(self) -> RPCEndpointReturnType:
        logging.info(f"Specification get request from {self.host}:{self.port}")

        return {"type": MessageType.OK.value, "content": self.specification}

    def dataflow_validate(self, dataflow: JsonType) -> RPCEndpointReturnType:
        logging.info(f"Dataflow validation request received from {self.host}:{self.port}")
        messages = DataflowValidator(dataflow).validate_kpm_design()
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

    def dataflow_run(self, dataflow: JsonType) -> RPCEndpointReturnType:
        logging.info(f"Dataflow run request received from {self.host}:{self.port}")
        errors = _kpm_dataflow_run_handler(dataflow, self.specification, self.build_dir)
        if errors:
            # note: only the first error is sent to the KPM frontend
            return {"type": MessageType.ERROR.value, "content": errors[0]}
        else:
            return {"type": MessageType.OK.value, "content": "Build succeeded"}

    def dataflow_stop(self, method: str) -> RPCEndpointReturnType:
        logging.info(f"Dataflow stop request from {self.host}:{self.port}")
        return {"type": MessageType.OK.value}

    def dataflow_export(self, dataflow: JsonType) -> RPCExportEndpointReturnType:
        logging.info(f"Dataflow export request received from {self.host}:{self.port}")

        filename = datetime.now().strftime("kpm_dataflow_%Y%m%d_%H%M%S.json")
        # TODO: We can't hide the "Save file" button, so let's just
        # make it save the dataflow JSON instead.
        flow_b64encoded = b64encode(json.dumps(dataflow).encode("utf-8")).decode("utf-8")
        return {"type": MessageType.OK.value, "content": flow_b64encoded, "filename": filename}

    def dataflow_import(
        self, external_application_dataflow: str, mime: str, base64: bool
    ) -> RPCEndpointReturnType:
        logging.info(f"Dataflow import request received from {self.host}:{self.port}")
        yaml_str = convert_message_to_string(external_application_dataflow, base64, mime)

        frontend = YamlFrontend()
        design_module = next(frontend.parse_str([yaml_str]))
        if not design_module.design:
            return {
                "type": MessageType.ERROR.value,
                "content": "Given design YAML file does not contain a design.",
            }

        dataflow = KpmDataflowBackend(self.specification)
        dataflow.represent_design(design_module.design, depth=-1)
        dataflow = dataflow.build()

        return {
            "type": MessageType.OK.value,
            "content": dataflow,
        }

    async def frontend_on_connect(self):
        """Gets run when frontend connects, loads initial design"""
        logging.debug("frontend on connect")
        if self.client is None:
            logging.debug("The client to send a request to is not defined")
            return
        if self.default_save_file.exists() and not self.initial_load:
            # User reloaded the page
            latest_dataflow = read_json_file(self.default_save_file)
            await self.client.request("graph_change", {"dataflow": latest_dataflow})
        elif self.design is not None:
            # Started topwrap with a design
            self.initial_load = False

            backend = KpmBackend(depth=-1)
            output = backend.represent(self.design.parent)

            if self.client is None:
                logging.debug("The client to send request to is not defined")
                return
            await self.client.request("graph_change", {"dataflow": output.dataflow})
        else:
            # Started topwrap without any design
            self.initial_load = False
            current_graph = await self.client.request("graph_get")
            # Save the current dataflow to save_file to ensure that the newest dataflow is there
            save_file_to_json(
                self.default_save_file.parent,
                self.default_save_file.name,
                current_graph["result"]["dataflow"],
            )

    async def nodes_on_change(self, **kwargs: Any):
        await _kpm_handle_graph_change(self)

    async def properties_on_change(self, **kwargs: Any):
        await _kpm_handle_graph_change(self)

    async def connections_on_change(self, **kwargs: Any):
        await _kpm_handle_graph_change(self)

    async def position_on_change(self, **kwargs: Any):
        await _kpm_handle_graph_change(self)


async def _kpm_handle_graph_change(rpc_object: RPCMethods):
    if rpc_object.client is None:
        return
    current_graph = await rpc_object.client.request("graph_get")
    save_file_to_json(
        rpc_object.default_save_file.parent,
        rpc_object.default_save_file.name,
        current_graph["result"]["dataflow"],
    )


def _kpm_dataflow_run_handler(data: JsonType, spec: JsonType, build_dir: Path) -> list[str]:
    """Parse information about design from KPM dataflow format into Topwrap's
    internal representation and build the design.
    """
    messages = DataflowValidator(data).validate_kpm_design()
    if not messages["errors"]:
        frontend = KpmFrontend()
        modules = frontend.parse_str([json.dumps(data), json.dumps(spec)])
        design = frontend.get_top_design(modules)

        backend = SystemVerilogBackend()
        repr = backend.represent(design.parent)
        out = next(backend.serialize(repr, combine=True))

        build_dir.mkdir(exist_ok=True)
        out.save(Path(build_dir))

        # TODO: No part or source dir specified here, because the user can't specify it when doing
        # the "run" action from KPM currently.
        fuse_builder = FuseSocBuilder(None)

        fuse_builder.add_source(out.filename, "systemVerilogSource")
        fuse_builder.build(design.parent.id.name, build_dir / f"{design.parent.id.name}.core")

    return messages["errors"]


async def kpm_run_client(
    rpc_params: RPCparams,
    client_ready_event: Optional[threading.Event] = None,
):
    client = CommunicationBackend(rpc_params.host, rpc_params.port)
    logging.debug("Initializing RPC client")
    await client.initialize_client(RPCMethods(rpc_params, client))
    if client_ready_event is not None:
        client_ready_event.set()
    logging.debug("starting json rpc client")
    await client.start_json_rpc_client()
