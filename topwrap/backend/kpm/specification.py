# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import asdict

from pipeline_manager.dataflow_builder.entities import Side
from pipeline_manager.specification_builder import (
    SpecificationBuilder,
    SpecificationBuilderException,
)

from topwrap.backend.kpm.common import (
    CLOCK_INTF_TYPE,
    EXT_COLOR,
    EXT_INTF_TYPE,
    INTF_COLOR,
    INTF_CONN_STYLE,
    PORT_COLOR,
    PORT_INTF_TYPE,
    ClockDomainMetanode,
    ConstMetanode,
    IdentifierMetanode,
    InterconnectMetanode,
    InverterMetanode,
    IoMetanode,
    KpmNodeAdditionalData,
    KpmNodeId,
    KpmPropertyType,
    LayerType,
    Metanode,
    ResetDomainMetanode,
    kpm_dir_from,
)
from topwrap.kpm_common import SPECIFICATION_VERSION
from topwrap.model.connections import PortDirection
from topwrap.model.interface import InterfaceMode
from topwrap.model.module import Module
from topwrap.util import JsonType

logger = logging.getLogger(__name__)


class KpmSpecificationBackend:
    _spec: SpecificationBuilder
    _io: IoMetanode
    _intr: InterconnectMetanode
    _interfaces: set[str]
    _modules: dict[str, Module]

    def __init__(self) -> None:
        self._spec = SpecificationBuilder(spec_version=SPECIFICATION_VERSION)
        self._interfaces = set()
        self._modules = dict()
        self._io = IoMetanode()
        self._intr = InterconnectMetanode()

    @classmethod
    def default(cls):
        """Instantiate an empty specification with all Topwrap-specific
        metadata and metanodes included."""

        self = cls()
        self._add_metadata()
        self._add_metanode(ConstMetanode())
        self._add_metanode(IdentifierMetanode())
        self._add_metanode(InverterMetanode())
        self._add_metanode(ClockDomainMetanode())
        self._add_metanode(ResetDomainMetanode())
        self._update_metanodes()
        return self

    def add_module(self, mod: Module, *, recursive: bool = False):
        """Add an IP `Module` to this specification as a node

        :param mod: the Module to add
        :param recursive: whether to recursively add nested submodules from inner designs as well
        """

        # Adding a duplicate module can happen when a module is both added explicitly, and is
        # brought in via recursive=True. E.g. when using `topwrap specification` like so:
        # `topwrap specification -d some/design.yaml some/ip/core.yaml`
        key = mod.id.combined()  # no version: matches KpmNodeId's node identity
        if key in self._modules:
            if self._modules[key].id != mod.id:
                logger.warning(
                    f"Module '{key}' version '{self._modules[key].id.version}' already added; "
                    f"skipping version '{mod.id.version}' (KPM node identity ignores version)."
                )
            return

        nid = KpmNodeId.from_ir_id(mod.id)
        nid = self._add_node(nid)
        self._modules[key] = mod
        self._spec.add_node_type_additional_data(
            nid.name, KpmNodeAdditionalData(full_module_id=asdict(mod.id))
        )

        for param in mod.parameters:
            val = param.default_value
            self._spec.add_node_type_property(
                nid.name, param.name, KpmPropertyType.TEXT.value, "" if val is None else val.value
            )

        for intf in mod.interfaces:
            self._add_interface(itype := intf.definition.id.combined())
            self._spec.add_node_type_interface(
                nid.name,
                intf.name,
                itype,
                kpm_dir_from(intf.mode).value,
                maxcount=1,
                side=Side.RIGHT.value if intf.mode == InterfaceMode.UNSPECIFIED else None,
            )

        clock_reset_ports = set(clock.clock._id for clock in mod.clocks) | set(
            reset.reset._id for reset in mod.resets
        )

        for port in mod.non_intf_ports():
            self._spec.add_node_type_interface(
                nid.name,
                port.name,
                [PORT_INTF_TYPE, CLOCK_INTF_TYPE]
                if port._id in clock_reset_ports
                else PORT_INTF_TYPE,
                kpm_dir_from(port.direction).value,
                maxcount=-1,
                side=Side.RIGHT.value if port.direction == PortDirection.INOUT else None,
            )

        for clock in mod.clocks:
            self._spec.add_node_type_property(
                nid.name, f"Domain for clock '{clock.name}'", KpmPropertyType.TEXT.value, "default"
            )

        for reset in mod.resets:
            self._spec.add_node_type_property(
                nid.name, f"Domain for reset '{reset.name}'", KpmPropertyType.TEXT.value, "default"
            )

        if recursive and mod.design is not None:
            for comp in mod.design.components:
                self.add_module(comp.module, recursive=True)

    def build(self) -> JsonType:
        return self._spec.create_and_validate_spec(skip_validation=True, sort_spec=True)

    def _add_node(self, nid: KpmNodeId) -> KpmNodeId:
        try:
            self._spec.add_node_type(nid.name, nid.category, LayerType.IP_CORE.value)
            return nid
        except SpecificationBuilderException as e:
            if "Redefined" in str(e) and not any(
                n["category"] == nid.category for n in self._spec._nodes.values()
            ):
                nid.name += " "
                return self._add_node(nid)
            raise

    def _update_metanodes(self):
        for n in (self._io, self._intr):
            if n.name in self._spec._nodes:
                del self._spec._nodes[n.name]
        intfs = [*sorted(self._interfaces)]
        for intf in self._io.interfaces:
            intf.interfacetype = [EXT_INTF_TYPE, PORT_INTF_TYPE] + intfs
        for intf in self._intr.interfaces:
            if intf.dynamic:
                intf.interfacetype = intfs[:]
        self._add_metanode(self._io)
        self._add_metanode(self._intr)

    def _add_metanode(self, meta: Metanode):
        layer = None if meta.layer is None else meta.layer.value
        self._spec.add_node_type(meta.name, meta.category, layer)
        if meta.style:
            self._spec.add_node_type_style(meta.name, meta.style)
        for intf in meta.interfaces:
            self._spec.add_node_type_interface(meta.name, **asdict(intf))
        for prop in meta.properties:
            args = asdict(prop)
            del args["group"]
            self._spec.add_node_type_property(meta.name, **args)
            for p in prop.group or ():
                args = asdict(p)
                del args["group"]
                del args["propname"]
                self._spec.add_node_type_property_group(
                    meta.name, prop.propname, p.propname, **args
                )

    def _add_interface(self, intf: str):
        if intf not in self._interfaces:
            self._interfaces.add(intf)
            self._update_metanodes()
            self._spec.metadata_add_interface_styling(intf, INTF_COLOR, INTF_CONN_STYLE.value)

    def _add_metadata(self):
        metadata = {
            "allowLoopbacks": True,
            "connectionStyle": "orthogonal",
            "movementStep": 15,
            "backgroundSize": 15,
            "layout": "CytoscapeEngine - grid",
            "twoColumn": True,
            "notifyWhenChanged": True,
            "welcome": False,
            "navbarItems": [
                {
                    "name": "Validate",
                    "stopName": "Stop",
                    "iconName": "Validate",
                    "procedureName": "dataflow_validate",
                    "allowToRunInParallelWith": ["dataflow_run", "custom_lint_files"],
                    "requireResponse": True,
                },
                {
                    "name": "Run",
                    "stopName": "Stop",
                    "iconName": "Run",
                    "procedureName": "dataflow_run",
                    "allowToRunInParallelWith": ["dataflow_validate", "custom_lint_files"],
                    "requireResponse": True,
                },
            ],
            "styles": {
                "inverter": {
                    "minimal": True,
                    "pill": {
                        "text": "Inverter",
                        "color": "#cccccc",
                    },
                }
            },
        }

        for meta_name, meta_value in metadata.items():
            self._spec.metadata_add_param(meta_name, meta_value)

        for layer in LayerType:
            self._spec.metadata_add_layer(layer.value, [layer.value])

        self._spec.metadata_add_layer("Clock and reset ports", [], [CLOCK_INTF_TYPE])

        self._spec.metadata_add_interface_styling(PORT_INTF_TYPE, PORT_COLOR)
        self._spec.metadata_add_interface_styling(CLOCK_INTF_TYPE, PORT_COLOR)
        self._spec.metadata_add_interface_styling(EXT_INTF_TYPE, EXT_COLOR)
