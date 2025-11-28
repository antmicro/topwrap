# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable, Iterator, Optional, Union, cast

import yaml
from pipeline_manager.dataflow_builder.dataflow_builder import (
    DataflowGraph,
    GraphBuilder,
)
from pipeline_manager.dataflow_builder.dataflow_graph import AttributeType
from pipeline_manager.dataflow_builder.entities import Direction as KpmDirection
from pipeline_manager.dataflow_builder.entities import Interface as KpmInterface
from pipeline_manager.dataflow_builder.entities import Node, NodeAttributeType, Property

from topwrap.backend.kpm.common import (
    ConstMetanode,
    IdentifierMetanode,
    InterconnectMetanode,
    InverterMetanode,
    IoMetanode,
)
from topwrap.backend.kpm.common import InterconnectMetanodeStrings as IMS
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.frontend.kpm.common import (
    KpmFrontendParseException,
    is_metanode,
    kpm_dir_to_ir_intf,
    kpm_dir_to_ir_port,
)
from topwrap.interconnects.types import INTERCONNECT_TYPES
from topwrap.kpm_common import SPECIFICATION_VERSION
from topwrap.model.connections import (
    Connection,
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    ReferencedInterface,
    ReferencedIO,
    ReferencedPort,
)
from topwrap.model.design import ModuleInstance
from topwrap.model.hdl_types import Bit, Logic
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import Interface, InterfaceDefinition
from topwrap.model.misc import ElaboratableValue, FileReference, Identifier, ObjectId
from topwrap.model.module import Design, Module
from topwrap.util import JsonType, UnreachableError

KpmIntfId = str


@dataclass(frozen=True)
class KpmUniqueInterface:
    """
    This class represents a unique instance of a KPM interface
    discriminated by both the graph and the interface itself.
    This is done because in KPM there can be multiple interfaces on
    different subgraph levels with the same ID.
    """

    graph: DataflowGraph
    interface: KpmInterface

    def __hash__(self) -> int:
        return hash((self.graph.id, self.interface.id))

    def __eq__(self, value: object) -> bool:
        if isinstance(value, KpmUniqueInterface):
            return self.graph.id == value.graph.id and self.interface.id == value.interface.id
        return NotImplemented


class _KpmDataflowInstanceData:
    """
    This class initially parses and holds various mappings between
    KPM and Topwrap entities that are crucial to correctly and efficiently
    parse the entire dataflow into an IR Module in ``KpmDataflowFrontend``.
    """

    #: Uses KPM dataflow builder API to parse raw dataflow
    flow: GraphBuilder

    #: Stores a mapping between a KPM interface and the IR endpoint
    #: (a port, an interface or a constant) that this KPM interface represents
    refmap: dict[KpmUniqueInterface, Union[ReferencedIO, ElaboratableValue]]

    #: Remembers which KPM interfaces were already handled by `_create_interconnect()`
    skip_iface_conns: list[KpmInterface]

    #: Holds a mapping between (KPM graph + KPM interface) and the KPM node owning that intf.
    intfnodemap: dict[KpmUniqueInterface, Node]

    #: Maps a KPM interface to every other interface connected to it
    intfconnmap: dict[KpmIntfId, list[KpmUniqueInterface]]

    def __init__(self, spec: JsonType, flow: JsonType):
        self.refmap = {}
        self.skip_iface_conns = []
        self.intfnodemap = {}
        self.intfconnmap = {}

        self.flow = GraphBuilder(spec, SPECIFICATION_VERSION)

        self.flow.load_graphs(flow, skip_validation=True)
        for graph in self.flow.graphs:
            for node in graph._nodes.values():
                for intf in node.interfaces:
                    self.intfnodemap[KpmUniqueInterface(graph, intf)] = node
            for conn in graph._connections.values():
                src, trg = conn.from_interface, conn.to_interface
                self.intfconnmap.setdefault(src.id, []).append(KpmUniqueInterface(graph, trg))
                self.intfconnmap.setdefault(trg.id, []).append(KpmUniqueInterface(graph, src))


class KpmDataflowFrontend:
    #: Internal specification created from loaded IR modules
    _spec: JsonType

    #: Holds a mapping between KPM node names and IR modules
    _modmap: dict[str, Module]

    #: An increasing counter of subgraphs encountered in the hierarchy.
    #: Used to generate an anonymous IR ``Identifier`` in case one
    #: wasn't provided by the user with the Identifier metanode.
    _subs: int
    _subgraph_cache: dict[str, Module]

    def __init__(self, modules: Iterable[Module]) -> None:
        """
        :param modules: A collection of modules which can potentially
            be used in subsequent dataflows.
        """

        super().__init__()
        self._modmap = {}
        self._subs = 0
        self._subgraph_cache = {}
        modids = {m.id: m for m in modules}

        spec = KpmSpecificationBackend.default()
        for mod in modules:
            spec.add_module(mod)
        for node in spec._spec._get_nodes(False):
            if (add := node.get("additionalData")) is not None:
                self._modmap[node["name"]] = modids[
                    Identifier(
                        name=add["full_module_id"].get("name"),
                        vendor=add["full_module_id"].get("vendor"),
                        library=add["full_module_id"].get("library"),
                    )
                ]
        self._spec = spec.build()

    def parse(self, dataflow: JsonType, source: Optional[Path] = None) -> Module:
        """
        Parses a structure representing a KPM dataflow
        into a top-level `Module` with a design.

        :param dataflow: The dataflow in the parsed JSON format
        """

        data = _KpmDataflowInstanceData(self._spec, dataflow)
        assert data.flow.entry_graph is not None
        return self._parse(source, data.flow.entry_graph, data)

    def _parse(
        self, source: Optional[Path], graph: DataflowGraph, data: _KpmDataflowInstanceData
    ) -> Module:
        mod = Module(
            id=Identifier(f"anon{self._subs}"),
            refs=[FileReference(source)] if source else (),
        )
        self._subs += 1
        mod.design = Design()

        unrealised_intrs = list[Node]()

        inverters = list[Node]()
        inverter_intfs = dict[KpmUniqueInterface, Node]()
        to_inverter_conns = dict[str, KpmUniqueInterface]()
        from_inverter_conns = dict[str, KpmUniqueInterface]()

        for node in graph._nodes.values():
            if not is_metanode(node.name):
                mod.design.add_component(self._create_mod_instance(source, graph, node, data))
            else:
                if node.name == InterconnectMetanode.name:
                    unrealised_intrs.append(node)
                elif node.name == ConstMetanode.name:
                    data.refmap[KpmUniqueInterface(graph, node.interfaces[0])] = ElaboratableValue(
                        node.properties[0].value
                    )
                elif node.name == IdentifierMetanode.name:
                    name = self._parse_property(node, "Name").value
                    vendor = self._parse_property(node, "Vendor").value
                    library = self._parse_property(node, "Library").value

                    mod.id = Identifier(name=name, vendor=vendor, library=library)
                elif node.name == IoMetanode.name:
                    if not any(itf.external_name is not None for itf in node.interfaces):
                        raise KpmFrontendParseException(
                            f"External IO metanode '{node.instance_name}'"
                            f"({node.id}) doesn't have an exposed interface"
                        )
                elif node.name == InverterMetanode.name:
                    inverters.append(node)
                    inverter_intfs[KpmUniqueInterface(graph, node.interfaces[0])] = node
                    inverter_intfs[KpmUniqueInterface(graph, node.interfaces[1])] = node

            for intf in node.interfaces:
                if intf.external_name is not None:
                    self._add_external(mod.design, KpmUniqueInterface(graph, intf), node, data)

        for node in unrealised_intrs:
            mod.design.add_interconnect(self._create_interconnect(graph, node, data))

        for conn in graph._connections.values():
            from_uniq = KpmUniqueInterface(graph, conn.from_interface)
            to_uniq = KpmUniqueInterface(graph, conn.to_interface)
            special_conn = False

            if from_uniq in inverter_intfs:
                from_inverter_conns[inverter_intfs[from_uniq].id] = to_uniq
                special_conn = True

            if to_uniq in inverter_intfs:
                to_inverter_conns[inverter_intfs[to_uniq].id] = from_uniq
                special_conn = True

            if special_conn:
                continue

            if (
                conn.from_interface not in data.skip_iface_conns
                and conn.to_interface not in data.skip_iface_conns
            ):
                mod.design.add_connection(
                    self._create_connection(
                        data.refmap.get(from_uniq),
                        data.refmap.get(to_uniq),
                    )
                )

        self._create_inverter_conns(mod, data, inverters, to_inverter_conns, from_inverter_conns)

        return mod

    def _create_inverter_conns(
        self,
        mod: Module,
        data: _KpmDataflowInstanceData,
        inverters: list[Node],
        to_inverter_conns: dict[str, KpmUniqueInterface],
        from_inverter_conns: dict[str, KpmUniqueInterface],
    ):
        assert mod.design is not None

        for node in inverters:
            if node.id not in to_inverter_conns:
                raise KpmFrontendParseException(
                    f"Inverter node ({node.id}) does not have anything connected to it's input"
                )

            if node.id not in from_inverter_conns:
                raise KpmFrontendParseException(
                    f"Inverter node ({node.id}) does not have anything connected to it's output"
                )

            from_intf = to_inverter_conns[node.id]
            to_intf = from_inverter_conns[node.id]

            if from_intf not in data.refmap:
                raise KpmFrontendParseException(
                    f"Inverter node ({node.id}) input is not connected to a module or external port"
                )

            if to_intf not in data.refmap:
                raise KpmFrontendParseException(
                    f"Inverter node ({node.id}) output is not connected to a "
                    "module or external port"
                )

            mod.design.add_connection(
                self._create_connection(
                    data.refmap.get(from_intf),
                    data.refmap.get(to_intf),
                    invert=True,
                )
            )

    def _create_mod_instance(
        self,
        source: Optional[Path],
        graph: DataflowGraph,
        node: Node,
        data: _KpmDataflowInstanceData,
    ) -> ModuleInstance:
        if node.subgraph is not None:
            subg = data.flow.get_graph_by_id(node.subgraph)
            module = self._subgraph_cache.get(subg.id)
            if module is None:
                module = self._parse(source, subg, data)
                self._subgraph_cache[subg.id] = module
        else:
            module = self._modmap.get(node.name)
            if module is None:
                raise KpmFrontendParseException(
                    f"Definition of module '{node.name}' not found in loaded modules"
                )

        inst = ModuleInstance(name=node.instance_name or node.name, module=module)

        for prop in node.properties:
            if (param := module.parameters.find_by_name(prop.name)) is not None:
                inst.parameters[param._id] = ElaboratableValue(prop.value)

        twints = {itf.name: itf for itf in module.interfaces}
        twports = {p.name: p for p in module.non_intf_ports()}
        for intf in node.interfaces:
            uintf = KpmUniqueInterface(graph, intf)
            if intf.name in twints:
                data.refmap[uintf] = ReferencedInterface(instance=inst, io=twints[intf.name])
            elif intf.name in twports:
                data.refmap[uintf] = ReferencedPort(instance=inst, io=twports[intf.name])

        return inst

    def _create_interconnect(
        self, graph: DataflowGraph, node: Node, data: _KpmDataflowInstanceData
    ) -> Interconnect:
        name = node.instance_name or InterconnectMetanode.name
        itype = INTERCONNECT_TYPES[self._parse_property(node, IMS.TYPE_PROP.value).value]
        params = self._parse_property(node, IMS.INTR_CONF_PROP.value).value
        params = itype.params.from_yaml("{" + params + "}")
        manparams = self._parse_property(node, IMS.INTR_MAN_CONF_PROP.value).value
        manparams = yaml.safe_load("{" + manparams + "}")
        subparams = self._parse_property(node, IMS.INTR_SUB_CONF_PROP.value).value
        subparams = yaml.safe_load("{" + subparams + "}")
        managers = dict[ObjectId[ReferencedInterface], itype.man_params]()
        subordinates = dict[ObjectId[ReferencedInterface], itype.sub_params]()
        clock = reset = None

        for intf in node.interfaces:
            data.skip_iface_conns.append(intf)
            for endpoint in data.intfconnmap.get(intf.id, ()):
                if endpoint.graph.id == graph.id:
                    other = data.refmap.get(KpmUniqueInterface(graph, endpoint.interface))
                    break
            else:
                other = data.refmap.get(KpmUniqueInterface(graph, intf))
            if intf.name == IMS.CLK_PORT.value:
                clock = other
            elif intf.name == IMS.RST_PORT.value:
                reset = other
            elif other is not None:
                if not isinstance(other, ReferencedInterface):
                    raise KpmFrontendParseException(
                        f"Interconnect '{node.instance_name}' interface '{intf.name}' is connected"
                        f" to '{type(other)}' instead of another interface."
                    )
                if (
                    match := re.match(
                        rf"((?:{IMS.MAN_INTF.value})|(?:{IMS.SUB_INTF.value}))\[(\d+)\]", intf.name
                    )
                ) is None:
                    raise UnreachableError
                mode, i = match.groups()
                i = int(i)
                if mode == IMS.MAN_INTF.value:
                    managers[other._id] = (
                        itype.man_params.from_dict(manparams[i])
                        if i in manparams
                        else itype.man_params()
                    )
                else:
                    subordinates[other._id] = (
                        itype.sub_params.from_dict(subparams[i])
                        if i in subparams
                        else itype.sub_params()
                    )

        if not isinstance(clock, ReferencedPort) or not isinstance(reset, ReferencedPort):
            raise KpmFrontendParseException(
                f"Interconnect '{name}' has invalid clock or reset connections"
            )

        return itype.intercon(
            name=name,
            params=params,
            clock=clock,
            reset=reset,
            managers=managers,
            subordinates=subordinates,
        )

    def _add_external(
        self, des: Design, kpm_intf: KpmUniqueInterface, node: Node, data: _KpmDataflowInstanceData
    ):
        assert kpm_intf.interface.external_name is not None

        twtype = next(self._infer_io_type(data, kpm_intf.graph, kpm_intf.interface), Bit())
        if isinstance(twtype, InterfaceDefinition):
            intf = Interface(
                name=kpm_intf.interface.external_name,
                mode=kpm_dir_to_ir_intf(kpm_intf.interface.direction),
                definition=twtype,
                signals={s._id: None for s in twtype.signals},
            )
            ref = ReferencedInterface.external(intf)
            des.parent.add_interface(intf)
        else:
            port = Port(
                name=kpm_intf.interface.external_name,
                direction=kpm_dir_to_ir_port(kpm_intf.interface.direction),
                type=twtype,
            )
            ref = ReferencedPort.external(port)
            des.parent.add_port(port)

        if node.name == IoMetanode.name:
            ext_intf = next(s for s in node.interfaces if s.external_name is not None)
            if ext_intf.direction == KpmDirection.INPUT:
                cont = node.get(NodeAttributeType.INTERFACE, direction=KpmDirection.OUTPUT)
            elif ext_intf.direction == KpmDirection.OUTPUT:
                cont = node.get(NodeAttributeType.INTERFACE, direction=KpmDirection.INPUT)
            else:
                cont = node.get(NodeAttributeType.INTERFACE, direction=KpmDirection.INOUT)
            data.refmap[KpmUniqueInterface(kpm_intf.graph, cast(KpmInterface, cont[0]))] = ref
        else:
            if (src := data.refmap.get(kpm_intf)) is not None:
                des.add_connection(self._create_connection(src, ref))
            data.refmap[kpm_intf] = ref

    def _create_connection(
        self,
        source: Optional[Union[ElaboratableValue, ReferencedIO]],
        target: Optional[Union[ElaboratableValue, ReferencedIO]],
        invert: bool = False,
    ) -> Connection:
        if isinstance(source, ElaboratableValue) and isinstance(target, ReferencedPort):
            if invert:
                raise KpmFrontendParseException(
                    f"Attempted to invert connection between port '{target.io.name}' "
                    f"and constant '{source.value}'"
                )
            return ConstantConnection(source, target)
        elif isinstance(source, ReferencedPort) and isinstance(target, ReferencedPort):
            return PortConnection(source, target, invert=invert)
        elif isinstance(source, ReferencedInterface) and isinstance(target, ReferencedInterface):
            if invert:
                raise KpmFrontendParseException(
                    f"Attempted to invert connection between interface '{source.io.name}' "
                    f"and interface '{target.io.name}'"
                )
            return InterfaceConnection(source, target)
        else:
            raise KpmFrontendParseException(
                "Invalid connection combination. Source is "
                f"'{type(source)}', target is '{type(target)}'."
            )

    def _parse_property(self, node: Node, propname: str) -> Property:
        return cast(Property, node.get(NodeAttributeType.PROPERTY, name=propname)[0])

    def _infer_io_type(
        self,
        data: _KpmDataflowInstanceData,
        graph: DataflowGraph,
        intf: KpmInterface,
        visited: Optional[set[KpmUniqueInterface]] = None,
    ) -> Iterator[Union[InterfaceDefinition, Logic]]:
        """
        Tries to infer if a KPM Interface represents an IR interface and gets
        its `InterfaceDefinition` or a `Logic` if it represents an IR port.
        It does that by recursively exploring every node connected to the respective
        KPM interface in search of a node that represents a known IR `Module`
        from which the information can be extracted.

        This method walks through the entire connection net of a port (crosses
        through external ports and different subgraph levels) in order to find a place
        where this net terminates on port with a known type (which always means an
        instance of a node from specification, whose definition is loaded in the IR).

        If this iterator does not return a result an assumption is made that this IO is a `Bit`
        """

        # avoid infinite loops
        if visited is None:
            visited = set()
        if (key := KpmUniqueInterface(graph, intf)) in visited:
            return
        visited.add(key)

        node = data.intfnodemap[key]
        intf = cast(KpmInterface, graph.get_by_id(AttributeType.INTERFACE, intf.id))

        if node.name == IoMetanode.name:
            for intf in node.interfaces:
                for uintf in data.intfconnmap.get(intf.id, ()):
                    yield from self._infer_io_type(data, uintf.graph, uintf.interface, visited)
        elif node.name == InterconnectMetanode.name:
            ports = [IMS.CLK_PORT.value, IMS.RST_PORT.value]
            for nintf in node.interfaces:
                if (
                    nintf.name in ports
                    and intf.name in ports
                    or nintf.name not in ports
                    and intf.name not in ports
                ):
                    for uintf in data.intfconnmap.get(nintf.id, ()):
                        yield from self._infer_io_type(data, uintf.graph, uintf.interface, visited)
        elif not is_metanode(node.name) and node.subgraph is not None:
            for uintf in data.intfconnmap.get(intf.id, ()):
                yield from self._infer_io_type(data, uintf.graph, uintf.interface, visited)
            subg = data.flow.get_graph_by_id(node.subgraph)
            # Find the corresponding interface inside the subgraph by matching external_name
            for subg_node in subg._nodes.values():
                for subg_intf in subg_node.interfaces:
                    if subg_intf.external_name == intf.name:
                        yield from self._infer_io_type(data, subg, subg_intf, visited)
                        break
        elif not is_metanode(node.name) and (mod := self._modmap.get(node.name)) is not None:
            for t in chain(mod.interfaces, mod.non_intf_ports()):
                if t.name == intf.name:
                    yield t.type if isinstance(t, Port) else t.definition
