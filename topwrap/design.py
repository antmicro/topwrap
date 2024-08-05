# amaranth: UnusedElaboratable=no

# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Collection,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import marshmallow
import marshmallow_dataclass
import yaml
from soc_generator.gen.wishbone_interconnect import WishboneRRInterconnect

from topwrap.common_serdes import optional_with
from topwrap.hdl_parsers_utils import PortDirection
from topwrap.ip_desc import IPCoreParameter

from .elaboratable_wrapper import ElaboratableWrapper
from .ipconnect import IPConnect
from .ipwrapper import IPWrapper


class InterconnectType(Enum):
    wishbone_roundrobin = WishboneRRInterconnect


@marshmallow_dataclass.dataclass(frozen=True)
class DesignIP:
    file: str
    module: str

    @property
    def path(self):
        return Path(self.file)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalPorts:
    input: List[str] = optional_with(list, {"data_key": "in"})
    output: List[str] = optional_with(list, {"data_key": "out"})
    inout: List[Tuple[str, str]] = optional_with(list)

    @cached_property
    def flat(self):
        return [*self.input, *self.output, *self.inout]

    @cached_property
    def as_dict(self):
        return {
            PortDirection.IN: self.input,
            PortDirection.OUT: self.output,
            PortDirection.INOUT: self.inout,
        }


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalIntfs:
    input: List[str] = optional_with(list, {"data_key": "in"})
    output: List[str] = optional_with(list, {"data_key": "out"})

    @cached_property
    def flat(self):
        return [*self.input, *self.output]

    @cached_property
    def as_dict(self):
        return {PortDirection.IN: self.input, PortDirection.OUT: self.output}


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalSection:
    ports: DesignExternalPorts = optional_with(DesignExternalPorts)
    interfaces: DesignExternalIntfs = optional_with(DesignExternalIntfs)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignSectionInterconnect:
    @marshmallow_dataclass.dataclass(frozen=True)
    class Slave:
        address: int
        size: int

    clock: Union[str, Tuple[str, str]]
    reset: Union[str, Tuple[str, str]]
    type: InterconnectType
    params: Dict[str, Any] = optional_with(dict)
    masters: Dict[str, List[str]] = optional_with(dict)
    slaves: Dict[str, Dict[str, Slave]] = optional_with(dict)


DS_PortsT = Dict[str, Dict[str, Union[int, str, Tuple[str, str]]]]
DS_InterfacesT = Dict[str, Dict[str, Union[str, Tuple[str, str]]]]


@marshmallow_dataclass.dataclass(frozen=True)
class DesignSection:
    name: Optional[str] = optional_with(
        None
    )  # This field is relevant only for the top-level design section
    parameters: Dict[str, Dict[str, IPCoreParameter]] = optional_with(dict)
    ports: DS_PortsT = optional_with(dict)
    interfaces: DS_InterfacesT = optional_with(dict)
    interconnects: Dict[str, DesignSectionInterconnect] = optional_with(dict)
    hierarchies: Dict[str, "DesignDescription"] = optional_with(dict)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignDescription:
    design: DesignSection = optional_with(DesignSection)
    external: DesignExternalSection = optional_with(DesignExternalSection)
    ips: Dict[str, DesignIP] = optional_with(dict)

    Schema: ClassVar[Type[marshmallow.Schema]] = marshmallow.Schema

    def generate_design(self, design_dir: Union[str, Path] = ".") -> IPConnect:
        design_dir = Path(design_dir)
        ipc = IPConnect()

        for hier_name, hier in self.design.hierarchies.items():
            hier_ipc = hier.generate_design(design_dir)
            ipc.add_component(hier_name, hier_ipc)

        for ip_name, ip in self.ips.items():
            ipc.add_component(
                ip_name,
                IPWrapper(
                    design_dir / ip.path,
                    ip.module,
                    ip_name,
                    self.design.parameters.get(ip_name, {}),
                ),
            )

        for intrcn_name, intrcn in self.design.interconnects.items():
            ipc.add_component(
                intrcn_name,
                ElaboratableWrapper(
                    name=intrcn_name, elaboratable=intrcn.type.value(**intrcn.params)
                ),
            )

        ipc.make_connections(self.design.ports, self.design.interfaces, self.external)
        ipc.make_interconnect_connections(self.design.interconnects, self.external)
        ipc.validate_inout_connections(self.external.ports.inout)
        return ipc

    @staticmethod
    def from_file(design_path: Union[str, Path]) -> "DesignDescription":
        design_path = Path(design_path)

        with open(design_path) as f:
            return DesignDescription.from_dict(yaml.safe_load(f))

    @staticmethod
    def from_dict(ast: Any) -> "DesignDescription":
        return cast(DesignDescription, DesignDescription.Schema().load(ast))

    def to_dict(self) -> Any:
        return cast(Any, self.Schema().dump(self))

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=True)

    def save(self, path: Optional[Union[str, Path]]):
        if path is None:
            if self.design.name is None:
                path = "top.yaml"
            else:
                path = self.design.name + ".yaml"

        with open(Path(path), "w") as f:
            f.write(self.to_yaml())


def build_design_from_yaml(
    design_path: Union[str, Path],
    build_dir: Union[str, Path],
    sources_dir: Collection[Union[str, Path]] = [],
    part: Optional[str] = None,
):
    design_path = Path(design_path)
    design_dir = design_path.parent
    build_dir = Path(build_dir)

    build_dir.mkdir(exist_ok=True)

    desc = DesignDescription.from_file(design_path)
    desc.generate_design(design_dir).build(
        build_dir=str(build_dir),
        sources_dir=sources_dir,
        part=part,
        top_module_name=desc.design.name or "top",
    )
