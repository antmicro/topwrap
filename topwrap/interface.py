# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from contextlib import nullcontext
from enum import Enum
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import marshmallow_dataclass
import yaml
from importlib_resources import as_file, files

from topwrap.util import recursive_defaultdict

from .common_serdes import (
    MarshmallowDataclassExtensions,
    RegexpT,
    ext_field,
    flatten_and_annotate,
)
from .config import config
from .hdl_parsers_utils import PortDirection


class InterfaceMode(Enum):
    MASTER = "master"
    SLAVE = "slave"
    UNSPECIFIED = "unspecified"


class InterfaceSignalType(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


@marshmallow_dataclass.dataclass(frozen=True)
class IfacePortSpecification(MarshmallowDataclassExtensions):
    """Specification of a port in an interface described in YAML interface definition file"""

    name: str
    regexp: RegexpT
    direction: PortDirection = ext_field(by_value=True)
    type: InterfaceSignalType = ext_field(by_value=True)


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinitionSignals(MarshmallowDataclassExtensions):
    @marshmallow_dataclass.dataclass(frozen=True)
    class Inner:
        input: Dict[str, RegexpT] = ext_field(dict, data_key="in")
        output: Dict[str, RegexpT] = ext_field(dict, data_key="out")
        inout: Dict[str, RegexpT] = ext_field(dict)

    required: Inner = ext_field(Inner)
    optional: Inner = ext_field(Inner)

    @cached_property
    def flat(self) -> List[IfacePortSpecification]:
        return [
            IfacePortSpecification.from_dict(port)
            for port in flatten_and_annotate(
                self.to_dict(), ["type", "direction", "name", "regexp"]
            )
        ]

    @staticmethod
    def from_flat(arr: List[IfacePortSpecification]) -> "InterfaceDefinitionSignals":
        data = recursive_defaultdict()
        for sig in arr:
            data[sig.type.value][sig.direction.value][sig.name] = sig.regexp
        return InterfaceDefinitionSignals.from_dict(data)


@marshmallow_dataclass.dataclass(frozen=True)
class InterfaceDefinition(MarshmallowDataclassExtensions):
    """Interface described in YAML interface definition file"""

    name: str
    port_prefix: str
    signals: InterfaceDefinitionSignals = ext_field(InterfaceDefinitionSignals)

    @cached_property
    def optional_signals(self) -> List[IfacePortSpecification]:
        return list(filter(lambda sig: sig.type == InterfaceSignalType.OPTIONAL, self.signals.flat))

    @cached_property
    def required_signals(self) -> List[IfacePortSpecification]:
        return list(filter(lambda sig: sig.type == InterfaceSignalType.REQUIRED, self.signals.flat))


def load_interface_definitions(dir_name: Optional[Path] = None):
    """Load interfaces described in YAML files, bundled with the package

    :param dir_name: directory that contains YAML files for interfaces
    :raises OSError: when dir_name directory cannot be listed
    :return: a list of dicts that represent the yaml files
    """

    defs = []
    with (
        as_file(files("topwrap.interfaces")) if dir_name is None else nullcontext(dir_name)
    ) as dir_name:
        for path in dir_name.glob("**/*.yaml"):
            with open(path) as f:
                defs.append(yaml.safe_load(f))
    return defs


@lru_cache(maxsize=None)
def get_predefined_interfaces() -> List[InterfaceDefinition]:
    return [InterfaceDefinition.from_dict(yaml_dict) for yaml_dict in load_interface_definitions()]


@lru_cache(maxsize=None)
def get_interfaces() -> List[InterfaceDefinition]:
    user_interfaces = []
    for path in config.get_interface_paths():
        user_interfaces += [
            InterfaceDefinition.from_dict(yaml_dict)
            for yaml_dict in load_interface_definitions(path)
        ]

    return user_interfaces + get_predefined_interfaces()


def get_interface_by_name(name: str) -> Optional[InterfaceDefinition]:
    """Retrieve interface definition by its name

    :return: `InterfaceDefinition` object, or `None` if there's no such interface
    """
    for definition in get_interfaces():
        if definition.name == name:
            return definition
    return None
