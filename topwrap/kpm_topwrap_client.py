# Copyright (c) 2023-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import threading
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional, TypedDict, Union, cast

from pipeline_manager_backend_communication.communication_backend import (
    CommunicationBackend,
)
from pipeline_manager_backend_communication.misc_structures import MessageType
from pipeline_manager_backend_communication.utils import convert_message_to_string
from typing_extensions import NotRequired

from topwrap.backend.backend import BackendOutputInfo
from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.common import IoMetanode
from topwrap.backend.yaml.backend import (
    IpCoreDescriptionBackend,
)
from topwrap.model.misc import Identifier, QuerableView
from topwrap.plugin.pipeline import BuildPipeline, OutputDir
from topwrap.plugin.steps import (
    KpmDataflowOutputStage,
    KpmSpecificationOutputStage,
    YamlDesignOutputStage,
)
from topwrap.util import JsonType

from .kpm_common import (
    RPCparams,
    check_for_iface_in_conn_graph,
    find_dataflow_node_by_id,
    get_graph_with_id,
    get_toplevel_graph,
)
from .kpm_dataflow_validator import DataflowValidator
from .util import read_json_file, save_file_to_json


class RPCEndpointReturnType(TypedDict):
    type: int
    content: NotRequired[Union[str, JsonType]]


class RPCExportEndpointReturnType(RPCEndpointReturnType):
    filename: str


class NonexistentNodeException(Exception):
    pass


class RPCMethods:
    def __init__(self, params: RPCparams, client: Optional[CommunicationBackend] = None):
        self.host = params.host
        self.port = params.port
        self.specification = params.specification
        self.build_dir = params.build_dir
        self.design = params.design
        self.extra_yamls = params.extra_yamls
        self.positions = params.positions
        self.client = client
        self.design_path = params.design_path
        # Use the $XDG_DATA_HOME as a destination for saving the dataflow, which defaults to
        # ~/.local/share
        xdg_data_home_var = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
        self.default_save_file = xdg_data_home_var / "topwrap/dataflow_latest_save.json"
        self.initial_load = True

    def app_capabilities_get(self) -> list[None]:
        return []

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

    async def dataflow_export(self, dataflow: JsonType) -> RPCExportEndpointReturnType:
        logging.info(f"Dataflow export request received from {self.host}:{self.port}")

        pipeline = BuildPipeline.kpm_yaml_pipeline()
        pipeline.prepare_str([json.dumps(self.specification)], json.dumps(dataflow))
        pipeline.process()

        ctx = pipeline.ctx
        assert ctx.top_module

        self.positions.update(ctx.positions)

        out_des, _ = cast(
            tuple[BackendOutputInfo, Optional[BackendOutputInfo]],
            ctx.outputs[YamlDesignOutputStage.name],
        )

        basename = (
            datetime.now()
            .strftime("design_{}_{}_{}_%Y%m%d_%H%M%S")
            .format(
                ctx.top_module.id.vendor,
                ctx.top_module.id.library,
                ctx.top_module.id.name,
            )
        )

        target_dir = Path(basename)
        target_dir.mkdir(exist_ok=True)

        pipeline.build(OutputDir(target_dir, target_dir))

        if self.client is not None:
            await self.client.request(
                "notification_send",
                {
                    "type": "info",
                    "title": "Design and positions YAML files saved",
                    "details": (
                        f"The design and positions YAML files have been saved to the {target_dir} "
                        "directory."
                    ),
                },
            )

        flow_b64encoded = b64encode(out_des.content.encode("utf-8")).decode("utf-8")
        return {
            "type": MessageType.OK.value,
            "content": flow_b64encoded,
            "filename": f"{basename}.yaml",
        }

    async def dataflow_import(
        self, external_application_dataflow: str, mime: str, base64: bool
    ) -> RPCEndpointReturnType:
        logging.info(f"Dataflow import request received from {self.host}:{self.port}")
        yaml_str = convert_message_to_string(external_application_dataflow, base64, mime)

        try:
            pipeline = BuildPipeline.yaml_kpm_pipeline(None)
            pipeline.prepare_str([open(f).read() for f in self.extra_yamls], yaml_str)
            pipeline.process()
        except Exception as e:
            return {
                "type": MessageType.ERROR.value,
                "content": str(e),
            }

        ctx = pipeline.ctx
        if ctx.top_module is None:
            return {
                "type": MessageType.ERROR.value,
                "content": "Given YAML file does not contain a design",
            }

        spec = cast(JsonType, ctx.outputs[KpmSpecificationOutputStage.name])
        flow = cast(JsonType, ctx.outputs[KpmDataflowOutputStage.name])
        self.design = ctx.top_module.design
        self.specification = spec
        self.positions.update(pipeline.ctx.positions)

        if self.client is not None:
            await self.client.request("specification_change", {"specification": self.specification})

        return {
            "type": MessageType.OK.value,
            "content": flow,
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

            backend = KpmBackend(depth=-1, positions=self.positions)
            output = backend.represent(self.design.parent)

            if self.client is None:
                logging.debug("The client to send request to is not defined")
                return

            self.specification = output.specification
            await self.client.request("specification_change", {"specification": self.specification})
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

    def custom_save_design_changes(self, dataflow: JsonType):
        """
        This procedure is run when the user wants to modify their
        design file in-place.
        """
        if self.design_path is None:
            return {
                "type": MessageType.ERROR.value,
                "content": "No design file loaded; cannot save changes",
            }
        # The KPM Frontend treats the graph defined in `entryGraph`
        # as the toplevel module. However, if the user goes into
        # a subgraph, that subgraph is now the entryGraph, but
        # we want to pass the whole design
        dataflow["entryGraph"] = get_toplevel_graph(dataflow)["id"]

        try:
            pipeline = BuildPipeline.kpm_yaml_pipeline()
            pipeline.prepare_str([json.dumps(self.specification)], json.dumps(dataflow))
            pipeline.process()
        except Exception as e:
            return {
                "type": MessageType.ERROR.value,
                "content": str(e),
            }

        ctx = pipeline.ctx
        if ctx.top_module is None:
            return {
                "type": MessageType.ERROR.value,
                "content": "Given dataflow seems to not contain a design",
            }

        out_des, out_pos = cast(
            tuple[BackendOutputInfo, BackendOutputInfo],
            ctx.outputs[YamlDesignOutputStage.name],
        )

        if out_pos is not None:
            out_pos.save(Path("."))

        def _extract_header(path: Path) -> str:
            res = ""
            with open(path, "r") as f:
                for line in f:
                    if line.startswith("#"):
                        res += line
                    else:
                        break
            return res + ("\n" if res else "")

        header = _extract_header(self.design_path)
        with NamedTemporaryFile("w", dir=".", delete=False) as f:
            f.write(header)
            f.write(out_des.content)
            tmp_path = f.name

        try:
            os.replace(tmp_path, self.design_path)
        except Exception:
            os.unlink(tmp_path)
            return {
                "type": MessageType.ERROR.value,
                "content": "Failed to save to design file",
            }

        return {
            "type": MessageType.OK.value,
            "content": f"Successfully saved changes to file {self.design_path}",
        }

    async def nodes_on_change(self, graph_id: str, nodes: JsonType, **kwargs: Any):
        logging.info("Node change event")
        diff = {"graph_id": graph_id, "nodes": nodes}
        await _kpm_handle_graph_change(self, None, diff)

    async def properties_on_change(self, **kwargs: Any):
        await _kpm_handle_graph_change(self)

    async def connections_on_change(self, graph_id: str, connections: JsonType):
        diff = {"graph_id": graph_id, "connections": connections}
        await _kpm_handle_graph_change(self, None, diff)

    async def position_on_change(self, **kwargs: Any):
        await _kpm_handle_graph_change(self)

    async def interfaces_on_change(self, **kwargs: Any):
        logging.info("Interface change event")
        await _kpm_handle_graph_change(self)

    async def graph_on_change(self, dataflow: JsonType):
        await _kpm_handle_graph_change(self, dataflow)

    # Only changes regarding the user-created graph are important
    # and saved, but in order to not cause warnings in the KPM GUI
    # all `[...]_on_[...]` RPC methods have to be implemented when `notifyWhenChanged` is True
    async def specification_on_change(self, **kwargs: Any):
        pass

    async def metadata_on_change(self, **kwargs: Any):
        pass

    async def viewport_on_center(self):
        pass

    async def nodes_on_highlight(self, **wargs: Any):
        pass

    def custom_download_ip(self, node_id: str) -> RPCExportEndpointReturnType:
        logging.info(f"IP export request received from {self.host}:{self.port}")

        latest_dataflow = read_json_file(self.default_save_file)

        clicked_node = find_dataflow_node_by_id(latest_dataflow, node_id)
        if clicked_node is None:
            raise NonexistentNodeException(f"There is no node with id {node_id}")

        node_type = QuerableView(self.specification["nodes"]).find_by(
            lambda n: n["name"] == clicked_node["name"]
        )
        if node_type is None:
            raise ValueError(f"Clicked node with nonexistent type {clicked_node['name']}")

        if (add := node_type.get("additionalData", None)) is None:
            raise KeyError("Selected IP node doesn't have additional data")
        id = Identifier(**add["full_module_id"])

        pipeline = BuildPipeline.kpm_yaml_pipeline()
        pipeline.prepare_str([json.dumps(self.specification)], json.dumps(latest_dataflow))
        pipeline.process()

        ctx = pipeline.ctx
        assert ctx.all_modules

        module = QuerableView(list(ctx.all_modules)).find_by_id_or_error(id)

        backend = IpCoreDescriptionBackend(ctx.existing_interfaces)

        repr = backend.represent(module)
        out = next(backend.serialize(repr))

        flow_b64encoded = b64encode(out.content.encode("utf-8")).decode("utf-8")
        return {"type": MessageType.OK.value, "content": flow_b64encoded, "filename": out.filename}

    def custom_download_hierarchy(self, node_id: str) -> RPCExportEndpointReturnType:
        logging.info(f"Hierarchy export request received from {self.host}:{self.port}")
        logging.debug(f"Hierarchy node id: {node_id}")

        latest_dataflow = read_json_file(self.default_save_file)
        clicked_node = find_dataflow_node_by_id(latest_dataflow, node_id)
        if clicked_node is None:
            raise NonexistentNodeException(f"There is no node with id {node_id}")

        subgraph_id = clicked_node["subgraph"]

        pipeline = BuildPipeline.kpm_yaml_pipeline(target_subgraph=subgraph_id)
        pipeline.prepare_str([json.dumps(self.specification)], json.dumps(latest_dataflow))
        pipeline.process()

        ctx = pipeline.ctx
        assert ctx.top_module

        out, _ = cast(
            tuple[BackendOutputInfo, Optional[BackendOutputInfo]],
            ctx.outputs[YamlDesignOutputStage.name],
        )
        logging.debug(f"Out type is: {type(out)}")

        flow_b64encoded = b64encode(out.content.encode("utf-8")).decode("utf-8")
        return {"type": MessageType.OK.value, "content": flow_b64encoded, "filename": out.filename}


async def _kpm_handle_graph_change(
    rpc_object: RPCMethods,
    current_graph: Optional[JsonType] = None,
    diff: Optional[JsonType] = None,
):
    if rpc_object.client is None:
        return
    if current_graph is None:
        response = await rpc_object.client.request("graph_get")
        current_graph = cast(JsonType, response["result"]["dataflow"])
        if diff is not None:
            if diff.get("nodes", None) is None:
                await _kpm_handle_connections_change(current_graph, diff, rpc_object)
            else:
                await _kpm_handle_nodes_change(current_graph, diff, rpc_object)
            response = await rpc_object.client.request("graph_get")
            current_graph = cast(JsonType, response["result"]["dataflow"])
    save_file_to_json(
        rpc_object.default_save_file.parent,
        rpc_object.default_save_file.name,
        current_graph,
    )


# Expose the unconnected interfaces of an "External I/O node"
# This function assumes it gets only external I/O metanodes
async def _expose_nodes(
    nodes: list[JsonType], new_dataflow: JsonType, graph_id: str, rpc_object: RPCMethods
) -> None:
    # If in is connected, expose out (and vice versa), if inout is connected expose inout
    opposite = {"in": "out", "out": "in", "inout": "inout"}
    if rpc_object.client is None:
        logging.debug("No client to expose nodes")
        return

    for node in nodes:
        connected = [
            iface
            for iface in node["interfaces"]
            if check_for_iface_in_conn_graph(new_dataflow, iface["id"], graph_id)
        ]
        interfaces = []
        if len(connected) == 0:
            for iface in node["interfaces"]:
                interfaces.append({"id": iface["id"]})
        elif len(connected) > 1:
            await rpc_object.client.request(
                "notification_send",
                {
                    "type": "warning",
                    "title": f"{node['instanceName']}: Too many connected interfaces",
                    "details": (
                        f"External I/O metanode {node['name']} should only have "
                        "one connected interface\n"
                        f"Node id is {node['id']}"
                    ),
                },
            )
            continue
        else:
            connected_iface = connected[0]  # This is OK: we check for list length earlier
            for iface in node["interfaces"]:
                if iface["name"] == opposite[connected_iface["name"]]:
                    external_name = node.get("instanceName", None)
                    if external_name is None or external_name == IoMetanode.name:
                        await rpc_object.client.request(
                            "notification_send",
                            {
                                "type": "warning",
                                "title": f"{node['name']}: Exposed interface cannot be named",
                                "details": (
                                    f"interface {iface['name']}(id {iface['id']}) "
                                    "cannot be named\n"
                                    f"Please give {node['name']}(id {node['id']}) "
                                    "a unique name\n"
                                    "Assigning temp name for now"
                                ),
                            },
                        )
                        external_name = f"{iface['name']}_{iface['id'][:6]}"
                    interfaces.append({"id": iface["id"], "externalName": external_name})
                else:
                    interfaces.append({"id": iface["id"]})
        await rpc_object.client.request(
            "interfaces_change",
            {"node_id": node["id"], "graph_id": graph_id, "interfaces": interfaces},
        )


async def _kpm_handle_connections_change(
    new_dataflow: JsonType, conns_diff: JsonType, rpc_object: RPCMethods
) -> None:
    """
    This function reacts to the `nodes_on_change` event from `KPM`.
    When a connection node is added, expose the interface opposite
    a connected interface
    """
    # Data for interfaces_change API call to KPM
    graph_id = conns_diff["graph_id"]
    graph = get_graph_with_id(new_dataflow, graph_id)
    if graph is None:
        return

    # Rerender exposed interfaces
    external_nodes = [node for node in graph["nodes"] if node["name"] == IoMetanode.name]
    await _expose_nodes(external_nodes, new_dataflow, graph_id, rpc_object)


async def _kpm_handle_nodes_change(
    new_dataflow: JsonType, nodes_diff: JsonType, rpc_object: RPCMethods
):
    """
    This function reacts to the `nodes_on_change` event from `KPM`.
    When an `External I/O` node is added, expose its unconnected interfaces
    via `interface_change` requests.
    """
    logging.info("Handling node change event")
    graph_id = nodes_diff["graph_id"]

    # When an `External I/O` node is added, expose its unconnected interfaces
    # This is always safe, even if the node was already there, as we check for
    # connection
    added_external = [
        node for node in nodes_diff["nodes"]["added"] if node["name"] == IoMetanode.name
    ]
    if len(added_external) > 0:
        await _expose_nodes(added_external, new_dataflow, graph_id, rpc_object)

    # There are two cases for what happens when a node is deleted:
    # 1. The node is deleted, its interfaces won't be shown
    # 2. The node is hidden (when going into a subgraph), its exposed
    #    interfaces should not be changes
    # In both cases we can just pass


def _kpm_dataflow_run_handler(
    data: JsonType,
    spec: JsonType,
    build_dir: Path,
) -> list[str]:
    """Parse information about design from KPM dataflow format into Topwrap's
    internal representation and build the design.
    """
    messages = DataflowValidator(data).validate_kpm_design()
    if not messages["errors"]:
        # TODO: No part or source dir specified here, because the user can't specify it when doing
        # the "run" action from KPM currently.
        pipeline = BuildPipeline.kpm_sv_pipeline(fuse=True, fuse_part=None, fuse_src_dirs=[])
        pipeline.run_str([json.dumps(spec)], json.dumps(data), OutputDir(build_dir, build_dir))

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
