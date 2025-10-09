# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar, Dict, Iterator, List, Optional, Tuple, Type, Union

import marshmallow
import marshmallow_dataclass

from topwrap.common_serdes import (
    MarshmallowDataclassExtensions,
    ResourcePathT,
    ext_field,
)
from topwrap.hdl_parsers_utils import PortDirection
from topwrap.interconnects.types import INTERCONNECT_TYPES
from topwrap.ip_desc import IPCoreDescription, IPCoreParameter


@marshmallow_dataclass.dataclass(frozen=True)
class DesignIP:
    file: ResourcePathT

    @cached_property
    def module(self):
        return IPCoreDescription.load(self.path)

    @property
    def path(self):
        return self.file.to_path()


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalPorts(MarshmallowDataclassExtensions):
    input: List[str] = ext_field(list, data_key="in")
    output: List[str] = ext_field(list, data_key="out")
    inout: List[Tuple[str, str]] = ext_field(list, inline_depth=1)

    @cached_property
    def flat(self):
        return [*self.input, *self.output, *self.inout]

    @cached_property
    def as_dict(self) -> Dict[PortDirection, Union[List[str], List[Tuple[str, str]]]]:
        return {
            PortDirection.IN: self.input,
            PortDirection.OUT: self.output,
            PortDirection.INOUT: self.inout,
        }


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalIntfs(MarshmallowDataclassExtensions):
    input: List[str] = ext_field(list, data_key="in")
    output: List[str] = ext_field(list, data_key="out")

    @cached_property
    def flat(self):
        return [*self.input, *self.output]

    @cached_property
    def as_dict(self):
        return {PortDirection.IN: self.input, PortDirection.OUT: self.output}


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalSection(MarshmallowDataclassExtensions):
    ports: DesignExternalPorts = ext_field(DesignExternalPorts)
    interfaces: DesignExternalIntfs = ext_field(DesignExternalIntfs)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignSectionInterconnect(MarshmallowDataclassExtensions):
    @marshmallow_dataclass.dataclass(frozen=True)
    class Subordinate:
        address: int
        size: int

    @marshmallow.validates("type")
    def _validate_type(self, type: str) -> bool:
        if type not in INTERCONNECT_TYPES:
            raise marshmallow.ValidationError(f"Invalid interconnect type: '{type}'")
        return True

    type: str
    clock: Union[str, Tuple[str, str]] = ext_field(inline_depth=0)
    reset: Union[str, Tuple[str, str]] = ext_field(inline_depth=0)
    params: Dict[str, Any] = ext_field(dict)
    managers: Dict[str, Union[List[str], Dict[str, Dict[str, Any]]]] = ext_field(dict)
    subordinates: Dict[str, Dict[str, Subordinate]] = ext_field(dict)


DS_PortsT = Dict[str, Dict[str, Union[int, str, Tuple[str, str]]]]
DS_InterfacesT = Dict[str, Dict[str, Union[str, Tuple[str, str]]]]


@marshmallow_dataclass.dataclass(frozen=True)
class DesignSection(MarshmallowDataclassExtensions):
    name: Optional[str] = ext_field(
        None
    )  # This field is relevant only for the top-level design section
    parameters: Dict[str, Dict[str, IPCoreParameter]] = ext_field(dict, deep_cleanup=True)
    ports: DS_PortsT = ext_field(dict, deep_cleanup=True, inline_depth=2)
    interfaces: DS_InterfacesT = ext_field(dict, deep_cleanup=True, inline_depth=2)
    interconnects: Dict[str, DesignSectionInterconnect] = ext_field(dict)
    hierarchies: Dict[str, "DesignDescription"] = ext_field(dict)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignDescription(MarshmallowDataclassExtensions):
    design: DesignSection = ext_field(DesignSection)
    external: DesignExternalSection = ext_field(DesignExternalSection)
    ips: Dict[str, DesignIP] = ext_field(dict)

    Schema: ClassVar[Type[marshmallow.Schema]] = marshmallow.Schema

    @property
    def all_ips(self) -> Iterator[DesignIP]:
        yield from self.ips.values()
        for hier in self.design.hierarchies.values():
            yield from hier.all_ips

    def save(self, path: Optional[Path] = None, **kwargs: Any):
        if path is None:
            if self.design.name is None:
                path = Path("top.yaml")
            else:
                path = Path(self.design.name + ".yaml")

        super().save(path, **kwargs)
