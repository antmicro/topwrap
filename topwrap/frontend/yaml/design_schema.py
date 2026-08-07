# Copyright (c) 2021-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from dataclasses import field, fields
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar, Dict, Iterator, List, Literal, Optional, Tuple, Type, Union

import marshmallow
import marshmallow_dataclass

from topwrap.backend.yaml.common.ip_core_schema import (
    IPCoreDescription,
    IPCoreParameter,
    IPCoreParameterField,
)
from topwrap.common_serdes import (
    HexInt,
    HexIntField,
    MarshmallowDataclassExtensions,
    ResourcePathT,
    ext_field,
)
from topwrap.hdl_parsers_utils import PortDirection
from topwrap.interconnects.types import INTERCONNECT_TYPES
from topwrap.model.config import ConfigDescription
from topwrap.model.misc import Identifier


@marshmallow_dataclass.dataclass(frozen=True)
class DesignIP(MarshmallowDataclassExtensions):
    file: ResourcePathT
    parameters: Dict[str, IPCoreParameter] = ext_field(
        dict,
        self_cleanup=True,
        deep_cleanup=True,
        marshmallow_field=marshmallow.fields.Dict(
            keys=marshmallow.fields.Str(),
            values=IPCoreParameterField(),
        ),
    )
    clocks: dict[str, str] = ext_field(dict)
    resets: dict[str, str] = ext_field(dict)

    @cached_property
    def module(self):
        return IPCoreDescription.load(self.path)

    @property
    def path(self):
        return self.file.to_path()


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalPortDefinition(MarshmallowDataclassExtensions):
    name: str
    dimensions: List[Tuple[Union[str, int], Union[str, int]]] = ext_field(list, inline_depth=1)


DesignExternalPort = Union[str, DesignExternalPortDefinition]


@marshmallow_dataclass.dataclass(frozen=True)
class DesignExternalPorts(MarshmallowDataclassExtensions):
    input: List[DesignExternalPort] = ext_field(list, data_key="in")
    output: List[DesignExternalPort] = ext_field(list, data_key="out")
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
        address: HexInt = field(metadata={"marshmallow_field": HexIntField()})
        size: HexInt = field(metadata={"marshmallow_field": HexIntField()})

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
    memory_map: Optional[str] = ext_field(None)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignSectionClockDomain(MarshmallowDataclassExtensions):
    signal: Union[str, Tuple[str, str]]


@marshmallow_dataclass.dataclass(frozen=True)
class DesignSectionResetDomain(MarshmallowDataclassExtensions):
    signal: Union[str, Tuple[str, str]]
    polarity: Union[Literal["active low"], Literal["active high"]]
    synchronous_to: Optional[str] = ext_field(None)


DS_PortsT = Dict[str, Dict[str, Union[int, str, Tuple[str, str]]]]
DS_InterfacesT = Dict[str, Dict[str, Union[str, Tuple[str, str]]]]


class PortsField(marshmallow.fields.Dict):
    def _serialize(self, value: DS_PortsT, attr: Optional[str], obj: Any, **kwargs: Any):
        for _, mod_data in value.items():
            for port, tgt in mod_data.items():
                if isinstance(tgt, tuple):
                    continue
                try:
                    tgt = int(tgt)
                except ValueError:
                    pass
                mod_data[port] = tgt
        return super()._serialize(value, attr, obj, **kwargs)


@marshmallow_dataclass.dataclass(frozen=True)
class ConnectionsSection(MarshmallowDataclassExtensions):
    ports: DS_PortsT = ext_field(
        dict, deep_cleanup=True, inline_depth=2, marshmallow_field=PortsField()
    )
    interfaces: DS_InterfacesT = ext_field(dict, deep_cleanup=True, inline_depth=2)


@marshmallow_dataclass.dataclass(frozen=True)
class MemoryMapEntry(MarshmallowDataclassExtensions):
    address: int
    params: dict[str, Any] = field(default_factory=dict)

    class Meta:
        unknown = marshmallow.INCLUDE

    @marshmallow.post_load()
    def collect_params(self, data: dict[str, Any], **kwargs: Dict[Any, Any]):
        known_fiels = {f.name for f in fields(MemoryMapEntry)}
        extra = {k: v for k, v in data.items() if k not in known_fiels}

        for k in extra:
            data.pop(k)
        data["params"] = extra

        return data


MemoryMapSubordinate = Union[MemoryMapEntry, dict[str, MemoryMapEntry]]
MemoryMap = dict[str, MemoryMapSubordinate]  # key is module_name


class DesignDescriptionSchema(marshmallow.Schema):
    """
    Schema class providing exception message formatting
    """

    def handle_error(
        self, error: marshmallow.ValidationError, data: Any, *, many: bool, **kwargs: Any
    ):
        SKIPPED_KEYS = ("value", "_schema")

        stack: list[tuple[Any, str]] = []
        final: list[tuple[str, str]] = []
        if type(error.messages) is not dict:
            raise TypeError
        for k in error.messages.keys():
            stack.append((error.messages[k], "{}".format(k)))
        while len(stack) > 0:
            last_el, last_str = stack.pop()
            if type(last_el) is dict:
                for k in last_el.keys():
                    new_str = "{}.{}".format(last_str, k) if k not in SKIPPED_KEYS else last_str
                    stack.append((last_el[k], new_str))
            elif type(last_el) is list:
                for err in last_el:
                    final.append((last_str, err))

        raise marshmallow.ValidationError(final)


@marshmallow_dataclass.dataclass(frozen=True, base_schema=DesignDescriptionSchema)
class DesignDescription(MarshmallowDataclassExtensions):
    name: Optional[str] = ext_field(
        None
    )  # This field is relevant only for the top-level design section
    vendor: Optional[str] = ext_field(None)
    library: Optional[str] = ext_field(None)
    ips: Dict[str, DesignIP] = ext_field(dict)
    connections: ConnectionsSection = ext_field(ConnectionsSection)
    interconnects: Dict[str, DesignSectionInterconnect] = ext_field(dict)
    clock_domains: Dict[str, DesignSectionClockDomain] = ext_field(dict)
    reset_domains: Dict[str, DesignSectionResetDomain] = ext_field(dict)
    external: DesignExternalSection = ext_field(DesignExternalSection)
    hierarchies: Dict[str, "DesignDescription"] = ext_field(dict)
    memory_maps: Dict[str, MemoryMap] = ext_field(dict)
    extensions: Dict[str, Any] = ext_field(dict)
    config: Optional[ConfigDescription] = ext_field(None)
    positions: Optional[str] = ext_field(None)

    Schema: ClassVar[Type[marshmallow.Schema]] = DesignDescriptionSchema

    @property
    def all_ips(self) -> Iterator[DesignIP]:
        yield from self.ips.values()
        for hier in self.hierarchies.values():
            yield from hier.all_ips

    def save(self, path: Optional[Path] = None, **kwargs: Any):
        if path is None:
            if self.name is None:
                path = Path("top.yaml")
            else:
                path = Path(self.name + ".yaml")

        super().save(path, **kwargs)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignInverterPosition(MarshmallowDataclassExtensions):
    source: Union[str, tuple[str, str]]
    target: Union[str, tuple[str, str]]
    position: tuple[float, float]


@marshmallow_dataclass.dataclass(frozen=True)
class DesignNodePosition(MarshmallowDataclassExtensions):
    name: str
    position: tuple[float, float]


@marshmallow_dataclass.dataclass(frozen=True)
class DesignPositionDefinition(MarshmallowDataclassExtensions):
    id: Identifier
    identifier: Optional[tuple[float, float]] = ext_field(None, inline_depth=0)
    components: list[DesignNodePosition] = ext_field(list, inline_depth=2)
    externals: list[DesignNodePosition] = ext_field(list, inline_depth=2)
    constants: list[DesignNodePosition] = ext_field(list, inline_depth=2)
    clock_domains: list[DesignNodePosition] = ext_field(list, inline_depth=2)
    reset_domains: list[DesignNodePosition] = ext_field(list, inline_depth=2)
    interconnects: list[DesignNodePosition] = ext_field(list, inline_depth=2)
    inverters: list[DesignInverterPosition] = ext_field(list, inline_depth=2)


@marshmallow_dataclass.dataclass(frozen=True)
class DesignPositions(MarshmallowDataclassExtensions):
    modules: list[DesignPositionDefinition]
