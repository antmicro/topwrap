# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from itertools import chain
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Union, cast

import marshmallow_dataclass
import yaml
from pipeline_manager.dataflow_builder.dataflow_builder import (
    DataflowGraph,
    GraphBuilder,
)
from pipeline_manager.dataflow_builder.entities import Direction, Node, Property, Side
from pipeline_manager.dataflow_builder.entities import Interface as KpmInterface

from topwrap.backend.kpm.common import (
    SUGBRAPH_NODE_NAME,
    ConstMetanode,
    IdentifierMetanode,
    InterconnectMetanode,
    InterconnectMetanodeStrings,
    IoMetanode,
    KpmNodeAdditionalData,
    kpm_dir_from,
)
from topwrap.common_serdes import MarshmallowDataclassExtensions, ext_field
from topwrap.kpm_common import SPECIFICATION_VERSION
from topwrap.model.connections import (
    Connection,
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
)
from topwrap.model.design import ModuleInstance
from topwrap.model.interconnect import Interconnect, InterconnectParams
from topwrap.model.interface import Interface
from topwrap.model.misc import Identifier, TranslationError
from topwrap.model.module import Design
from topwrap.util import JsonType


@marshmallow_dataclass.dataclass
class _Cleaner(MarshmallowDataclassExtensions):
    inner: dict[Any, Any] = ext_field(deep_cleanup=True)


class KpmDataflowBackendException(TranslationError):
    pass


class KpmNodeNotFound(KpmDataflowBackendException):
    pass


_REFTYPE = dict[tuple[Optional[ModuleInstance], int], KpmInterface]


class KpmDataflowBackend:
    flow: GraphBuilder
    _spec: JsonType

    # Maps between specification `Identifier`s and specification node names
    _nodeids: dict[str, str]

    def __init__(self, specification: JsonType) -> None:
        """
        :param specification: The specification to base this dataflow on
        """

        super().__init__()
        self._spec = specification
        self._nodeids = {}
        self._refx = {}

        for node in self._spec["nodes"]:
            add: Optional[KpmNodeAdditionalData] = node.get("additionalData")
            if add is not None:
                self._nodeids[Identifier(**add["full_module_id"]).combined()] = node["name"]

        with NamedTemporaryFile("w+") as f:
            json.dump(specification, f)
            f.flush()
            self.flow = GraphBuilder(Path(f.name), SPECIFICATION_VERSION)

    def build(self) -> JsonType:
        return cast(JsonType, self.flow.to_json(False))

    def represent_design(self, design: Design, *, depth: int = 0) -> DataflowGraph:
        """
        Make this dataflow represent the given `Design`

        :param design: The design
        :param depth: How many nested levels of subgraphs to generate to represent hierarchies.
            Instances of modules that have an associated `Design` will be realised as subgraphs,
            instead of regular instances of nodes from the specification. This has its own limitations,
            such as not being able to set properties on subgraphs.

            Setting this to any negative value is equivalent to a depth of infinity.
        """
        self.flow.graphs.clear()
        graph = self.flow.create_graph()

        return self._represent_design(design, graph, depth=depth)

    def _represent_design(
        self, design: Design, graph: DataflowGraph, depth: int = 0
    ) -> DataflowGraph:
        ref: _REFTYPE = {}
        self.add_id_node(graph, design.parent.id)

        for comp in design.components:
            self.add_component(graph, comp, depth, ref)

        for ext_intf in design.parent.interfaces:
            self.add_external(graph, ext_intf, ref)

        for ext_port in design.parent.non_intf_ports():
            self.add_external(graph, ext_port, ref)

        for conn in design.connections:
            self.add_connection(graph, conn, ref)

        for intr in design.interconnects:
            self.add_interconnect(graph, intr, ref)

        return graph

    def add_id_node(self, graph: DataflowGraph, id: Identifier):
        node = graph.create_node(name=IdentifierMetanode.name)
        node.set_property(IdentifierMetanode().properties[0].propname, id.name)
        node.set_property(IdentifierMetanode().properties[1].propname, id.vendor)
        node.set_property(IdentifierMetanode().properties[2].propname, id.library)

    def add_component(self, graph: DataflowGraph, comp: ModuleInstance, depth: int, refs: _REFTYPE):
        node_name, subg = self._nodeids.get(comp.module.id.combined()), None

        if depth != 0 and comp.module.design is not None or node_name is None:
            subg = self.flow.create_graph()
            # ugly workaround for the lack of subgraph functionality inside dataflow builder
            node = graph.create_node(
                name=IoMetanode.name,
                instance_name=comp.name,
                interfaces=[],
                properties=[
                    Property(p.name, p.default_value.value if p.default_value is not None else "")
                    for p in comp.module.parameters
                ],
            )
            node.subgraph = subg._id
            node._node_name = SUGBRAPH_NODE_NAME
            des = Design()
            des.parent = comp.module
            self._represent_design(comp.module.design or des, subg, depth - 1)
        else:
            node = graph.create_node(name=node_name, instance_name=comp.name, interfaces=[])

        for param, val in comp.parameters.items():
            node.set_property(param.resolve().name, val.value)

        ir_io = {
            io.name: io
            for io in cast(
                list[Union[Port, Interface]], [*comp.module.ports, *comp.module.interfaces]
            )
        }
        for intf in chain(comp.module.interfaces, comp.module.non_intf_ports()):
            dir = kpm_dir_from(intf.direction if isinstance(intf, Port) else intf.mode)
            intf = KpmInterface(
                name=intf.name,
                direction=dir,
                side=Side.LEFT if dir == Direction.INPUT else Side.RIGHT,
            )
            node.interfaces.append(intf)
            if subg is not None:
                for node_name in subg._nodes.values():
                    if node_name.name == IoMetanode.name:
                        for nintf in node_name.interfaces:
                            if intf.name == nintf.external_name:
                                intf.id = nintf.id
            refs[(comp, id(ir_io[intf.name]))] = intf

    def add_external(
        self, graph: DataflowGraph, io: Union[Port, Interface], refs: _REFTYPE
    ) -> Node:
        interfaces = [
            KpmInterface(i.interfacename, kpm_dir_from(i.direction))
            for i in IoMetanode().interfaces
        ]

        intf_in, intf_out, intf_inout = interfaces
        dir = kpm_dir_from(io.direction if isinstance(io, Port) else io.mode)
        if dir == Direction.INPUT:
            exposed, target = intf_in, intf_out
        elif dir == Direction.OUTPUT:
            exposed, target = intf_out, intf_in
        else:
            exposed, target = intf_inout, intf_inout

        exposed.external_name = io.name

        node = graph.create_node(name=IoMetanode.name, instance_name=io.name, interfaces=interfaces)

        refs[(None, id(io))] = target
        return node

    def add_connection(self, graph: DataflowGraph, conn: Connection, ref: _REFTYPE):
        if isinstance(conn, ConstantConnection):
            node = graph.create_node(name=ConstMetanode.name)
            node.set_property(ConstMetanode().properties[0].propname, conn.source.value)
            port = conn.target.io
            if port is None:
                raise TranslationError("Connection to Logic with an unreferenced port")
            self._connect(graph, node.interfaces[0], ref[(conn.target.instance, id(port))])
        elif isinstance(conn, PortConnection):
            port1 = conn.source.io
            port2 = conn.target.io
            if port1 is None or port2 is None:
                raise TranslationError("Connection to Logic with an unreferenced port")
            self._connect(
                graph,
                ref[(conn.source.instance, id(port1))],
                ref[(conn.target.instance, id(port2))],
            )
        elif isinstance(conn, InterfaceConnection):
            self._connect(
                graph,
                ref[(conn.source.instance, id(conn.source.io))],
                ref[(conn.target.instance, id(conn.target.io))],
            )

    def add_interconnect(self, graph: DataflowGraph, intr: Interconnect, ref: _REFTYPE):
        node = graph.create_node(name=InterconnectMetanode.name, instance_name=intr.name)
        mprop, sprop = InterconnectMetanode().interfaces[2:]
        node.interfaces = [
            KpmInterface("clk", Direction.INPUT),
            KpmInterface("rst", Direction.INPUT),
        ]

        self._connect(
            graph,
            node.interfaces[0],
            ref[(intr.clock.instance, id(intr.clock.io))],
        )
        self._connect(
            graph,
            node.interfaces[1],
            ref[(intr.reset.instance, id(intr.reset.io))],
        )

        # ugly workaround for dynamic interfaces not being supported
        for prop, cons in ((mprop, intr.managers), (sprop, intr.subordinates)):
            node.properties.append(
                Property(f"{prop.interfacename} {prop.direction} count", len(cons))
            )
            for i, (intf, _params) in enumerate(cons.items()):
                refi = intf.resolve()
                intf = KpmInterface(f"{prop.interfacename}[{i}]", kpm_dir_from(prop.direction))
                node.interfaces.append(intf)
                self._connect(graph, intf, ref[(refi.instance, id(refi.io))])
        ##

        for pname, params in (
            (InterconnectMetanodeStrings.INTR_CONF_PROP, intr.params),
            (InterconnectMetanodeStrings.INTR_MAN_CONF_PROP, intr.managers.values()),
            (InterconnectMetanodeStrings.INTR_SUB_CONF_PROP, intr.subordinates.values()),
        ):
            if not isinstance(params, InterconnectParams):
                params = _Cleaner({i: x.to_dict() for i, x in enumerate(params)}).to_dict()["inner"]
            else:
                params = params.to_dict()
            set = yaml.safe_dump(params, default_flow_style=True).strip()[1:-1]
            node.properties.append(Property(pname.value, set))

    def _connect(self, graph: DataflowGraph, i1: KpmInterface, i2: KpmInterface):
        if i1.direction == Direction.INPUT:
            i1, i2 = i2, i1
        graph.create_connection(i1, i2)
