# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Iterable, Iterator, Optional, cast

from pipeline_manager.dataflow_builder.entities import Direction

from topwrap.backend.kpm.common import PORT_INTF_TYPE, LayerType
from topwrap.frontend.kpm.common import (
    KpmFrontendParseException,
    kpm_dir_to_ir_intf,
    kpm_dir_to_ir_port,
)
from topwrap.frontend.kpm.dataflow import KpmDataflowFrontend
from topwrap.kpm_common import SPECIFICATION_VERSION
from topwrap.model.connections import Port
from topwrap.model.interface import Interface, InterfaceDefinition
from topwrap.model.misc import (
    ElaboratableValue,
    FileReference,
    Identifier,
    Parameter,
)
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
        self,
        spec: JsonType,
        *,
        allow_unknown_intfs: bool = True,
        resolve_graphs: bool = True,
        source: Optional[Path] = None,
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
                *self.parse(
                    spec,
                    allow_unknown_intfs=allow_unknown_intfs,
                    resolve_graphs=False,
                    source=source,
                )
            ]
            front = KpmDataflowFrontend(modules)
            # Pass all graphs together so nested subgraph references can be resolved
            yield front.parse({"graphs": graphs})
            yield from modules
            return

        node: JsonType
        for node in spec.get("nodes", []):
            if node.get("layer", "") != LayerType.IP_CORE.value:
                continue

            add = node.get("additionalData", None)
            if add is None:
                raise KpmFrontendParseException(
                    f"Node {node['name']} lacks additionalData vith VLNV"
                )
            mod = Module(
                id=Identifier(**add["full_module_id"]),
                refs=[FileReference(source)] if source else (),
            )

            prop: JsonType
            for prop in node.get("properties", ()):
                # skip clock/reset domain assignment properties
                if prop["name"].startswith("Domain for"):
                    continue
                mod.add_parameter(
                    Parameter(name=prop["name"], default_value=ElaboratableValue(prop["default"]))
                )

            intf: JsonType
            for intf in node.get("interfaces", ()):
                type: str = ""
                if isinstance(intf["type"], str):
                    type = intf["type"]
                elif PORT_INTF_TYPE in intf["type"]:
                    type = PORT_INTF_TYPE
                else:
                    raise KpmFrontendParseException(
                        f"Unexpected KPM interface type '{intf['type']}'"
                    )

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
