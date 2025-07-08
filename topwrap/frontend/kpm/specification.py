# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Iterable, Iterator, cast

from pipeline_manager.dataflow_builder.entities import Direction

from topwrap.backend.kpm.common import PORT_INTF_TYPE, KpmNodeAdditionalData, LayerType
from topwrap.frontend.kpm.common import (
    KpmFrontendParseException,
    kpm_dir_to_ir_intf,
    kpm_dir_to_ir_port,
)
from topwrap.frontend.kpm.dataflow import KpmDataflowFrontend
from topwrap.kpm_common import SPECIFICATION_VERSION
from topwrap.model.connections import Port
from topwrap.model.interface import Interface, InterfaceDefinition
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module
from topwrap.util import JsonType

logger = logging.getLogger(__name__)


class KpmSpecificationFrontend:
    _intfmap: dict[str, InterfaceDefinition]

    def __init__(self, intfs: Iterable[InterfaceDefinition] = ()) -> None:
        """
        :param intfs: A collection of interface definitions that
            can be used by subsequent KPM specification nodes
        """

        super().__init__()
        self._intfmap = {d.id.combined(): d for d in intfs}

    def parse(
        self, spec: JsonType, *, allow_unknown_intfs: bool = True, resolve_graphs: bool = True
    ) -> Iterator[Module]:
        """
        Parse a KPM specification into multiple IR modules.

        :param spec: The specification in the parsed JSON format
        :param allow_unknown_intfs: If True, KPM interfaces that represent IR interfaces
            but have no known definition loaded will be represented as a `Bit` port.
            Otherwise an exception will be raised.
        :param resolve_graphs: If True, graphs under the "graphs" field in the
            specification will be resolved and yielded as top-level modules with
            designs by the dataflow frontend. Otherwise they'll be ignored.
        """

        if (vers := spec.get("version", None)) != SPECIFICATION_VERSION:
            logger.warning(
                f"Trying to load KPM specification version '{vers}'. The "
                f"version currently supported by Topwrap is '{SPECIFICATION_VERSION}'."
            )
        if "includeGraphs" in spec or "include" in spec:
            logger.warning("Remote includes in the KPM specification are not supported")

        if len((graphs := spec.get("graphs", ()))) > 0 and resolve_graphs:
            modules = [
                *self.parse(spec, allow_unknown_intfs=allow_unknown_intfs, resolve_graphs=False)
            ]
            front = KpmDataflowFrontend(modules)
            for graph in graphs:
                yield front.parse({"graphs": [graph]})
            yield from modules
            return

        node: JsonType
        for node in spec.get("nodes", []):
            if node.get("layer", "") != LayerType.IP_CORE.value:
                continue

            add: KpmNodeAdditionalData = node["additionalData"]
            mod = Module(
                id=Identifier(
                    name=add["full_module_id"]["name"],
                    vendor=add["full_module_id"]["vendor"],
                    library=add["full_module_id"]["library"],
                )
            )

            prop: JsonType
            for prop in node.get("properties", ()):
                mod.add_parameter(
                    Parameter(name=prop["name"], default_value=ElaboratableValue(prop["default"]))
                )

            intf: JsonType
            for intf in node.get("interfaces", ()):
                type: str = intf["type"]
                dir = cast(
                    Direction,
                    Direction._value2member_map_[intf.get("direction", Direction.INOUT.value)],
                )
                if (idef := self._intfmap.get(type)) is not None:
                    mod.add_interface(
                        Interface(
                            name=intf["name"],
                            mode=kpm_dir_to_ir_intf(dir),
                            definition=idef,
                            signals={s._id: None for s in idef.signals},
                        )
                    )
                elif type == PORT_INTF_TYPE or allow_unknown_intfs:
                    if type != PORT_INTF_TYPE:
                        logger.warning(
                            f"KPM interface '{intf['name']}' for module '{mod.id}' references"
                            f" an IR interface of type '{intf['type']}', but a definition for"
                            f" such an interface does not exist or is not loaded"
                        )
                    mod.add_port(Port(name=intf["name"], direction=kpm_dir_to_ir_port(dir)))
                else:
                    raise KpmFrontendParseException(
                        "KPM interface represents an IR interface, but no such"
                        " interface definition exists"
                    )

            yield mod
