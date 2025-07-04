# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from functools import cached_property, lru_cache
from typing import Dict, List, Optional

import marshmallow_dataclass

from topwrap.repo.user_repo import InterfaceDescription, UserRepo
from topwrap.util import get_config, recursive_defaultdict

from .common_serdes import (
    MarshmallowDataclassExtensions,
    RegexpT,
    ext_field,
    flatten_and_annotate,
)
from .config import config
from .hdl_parsers_utils import PortDirection


class InterfaceMode(Enum):
    MANAGER = "manager"
    SUBORDINATE = "subordinate"
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

    @staticmethod
    @lru_cache(maxsize=None)
    def get_builtins() -> Dict[str, "InterfaceDefinition"]:
        """Loads all builtin internal interfaces

        :return: a dict where keys are the interface names and values are the InterfaceDefinition
            objects
        """

        intfs: Dict[str, InterfaceDefinition] = {}

        repo = get_config().builtin_repo
        for intf in repo.get_resources(InterfaceDescription):
            intfs[intf.name] = InterfaceDefinition.load(intf.file.path)
        return intfs


@lru_cache(maxsize=None)
def get_interfaces() -> List[InterfaceDefinition]:
    user_interfaces = []
    for repo_entry in config.repositories.values():
        repo = UserRepo()
        repo.load(repo_entry.to_path())
        for desc in repo.get_resources(InterfaceDescription):
            user_interfaces.append(InterfaceDefinition.load(desc.file.path))

    return user_interfaces


def get_interface_by_name(name: str) -> Optional[InterfaceDefinition]:
    """Retrieve interface definition by its name

    :return: `InterfaceDefinition` object, or `None` if there's no such interface
    """
    for definition in get_interfaces():
        if definition.name == name:
            return definition
    return None
