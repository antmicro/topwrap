# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from dataclasses import field
from enum import Enum
from typing import List, Optional

import marshmallow
import marshmallow_dataclass

from .common_serdes import (
    RegexpT,
    annotate_flat_tree,
    flatten_tree,
    unflatten_annotated_tree,
)
from .hdl_parsers_utils import PortDirection
from .parsers import parse_interface_definitions


class InterfaceMode(Enum):
    MASTER = "master"
    SLAVE = "slave"
    UNSPECIFIED = "unspecified"


class InterfaceSignalType(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


@marshmallow_dataclass.dataclass(frozen=True)
class IfacePortSpecification:
    """Specification of a port in an interface described in YAML interface definition file"""

    name: str
    regexp: RegexpT
    direction: PortDirection = field(metadata={"by_value": True})
    type: InterfaceSignalType = field(metadata={"by_value": True})


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinition:
    """Interface described in YAML interface definition file"""

    name: str
    port_prefix: str
    signals: List[IfacePortSpecification] = field(default_factory=list)

    YAML_GROUPING_ORDER = ["type", "direction", "name", "regexp"]

    @marshmallow.pre_load
    def flatten_signals(self, data, many, **kwargs):
        try:
            data["signals"] = annotate_flat_tree(
                flatten_tree(data["signals"]), InterfaceDefinition.YAML_GROUPING_ORDER
            )
        except ValueError as e:
            # reraise as marshmallow exception
            raise marshmallow.ValidationError(str(e))

        return data

    @marshmallow.post_dump
    def unflatten_signals(self, data, many, **kwargs):
        data["signals"] = unflatten_annotated_tree(
            data["signals"], InterfaceDefinition.YAML_GROUPING_ORDER
        )
        return data

    @property
    def optional_signals(self) -> List[IfacePortSpecification]:
        return list(filter(lambda sig: sig.type == InterfaceSignalType.OPTIONAL, self.signals))

    @property
    def required_signals(self) -> List[IfacePortSpecification]:
        return list(filter(lambda sig: sig.type == InterfaceSignalType.REQUIRED, self.signals))


# this holds all predefined interfaces
interface_definitions = [
    InterfaceDefinition.Schema().load(yaml_dict) for yaml_dict in parse_interface_definitions()
]


def get_interface_by_name(name: str) -> Optional[InterfaceDefinition]:
    """Retrieve a predefined interface definition by its name

    :return: `InterfaceDefinition` object, or `None` if there's no such interface
    """
    for definition in interface_definitions:
        if definition.name == name:
            return definition
    return None


def check_interface_compliance(iface_def: InterfaceDefinition, signals: dict) -> bool:
    """Check if list of signal names matches the names in interface definition"""

    for sig in iface_def.required_signals:
        if sig.name not in signals[sig.direction.value]:
            return False
    for direction in ["in", "out", "inout"]:
        for name in signals.get(direction, []):
            if name not in [sig.name for sig in iface_def.signals]:
                return False
    return True
