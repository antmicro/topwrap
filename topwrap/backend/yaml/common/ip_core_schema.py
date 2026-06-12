# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from functools import cached_property
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Collection,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

import marshmallow
import marshmallow_dataclass

from topwrap.backend.yaml.common.interface_schema import InterfaceModeDescription
from topwrap.common_serdes import MarshmallowDataclassExtensions, ext_field
from topwrap.hdl_parsers_utils import PortDefinition as LegacyPortDefinition
from topwrap.hdl_parsers_utils import PortDirection as LegacyPortDirection
from topwrap.model.interface import (
    InterfaceMode,
)
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.repo.exceptions import ResourceNotFoundException
from topwrap.util import get_config, get_interface_by_id

_StrOrInt = Union[str, int]


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreComplexSignal(MarshmallowDataclassExtensions):
    name: str
    bound: Optional[tuple[_StrOrInt, _StrOrInt]] = ext_field(None)
    slice: Optional[tuple[_StrOrInt, _StrOrInt]] = ext_field(None)
    default: Optional[Union[int, str]] = ext_field(None)


Signal = Union[
    str,
    Tuple[str, _StrOrInt, _StrOrInt],
    Tuple[str, _StrOrInt, _StrOrInt, _StrOrInt, _StrOrInt],
    IPCoreComplexSignal,
]


@marshmallow_dataclass.dataclass(frozen=True)
class IPCorePort:
    name: str
    upper_bound: _StrOrInt
    lower_bound: _StrOrInt
    upper_slice: _StrOrInt
    lower_slice: _StrOrInt
    direction: LegacyPortDirection = ext_field(by_value=True)

    @property
    def bounds(self) -> Tuple[_StrOrInt, _StrOrInt, _StrOrInt, _StrOrInt]:
        return (self.upper_bound, self.lower_bound, self.upper_slice, self.lower_slice)

    @cached_property
    def raw(self) -> Signal:
        out = self.bounds
        if out == (0, 0, 0, 0):
            out = self.name
        elif out[:2] == out[2:]:
            out = (self.name, *out[:2])
        else:
            out = (self.name, *out)
        return out

    @staticmethod
    def from_sig_and_dir(sig: Signal, dir: LegacyPortDirection) -> "IPCorePort":
        if isinstance(sig, IPCoreComplexSignal):
            return IPCorePort(
                name=sig.name,
                direction=dir,
                upper_bound=sig.bound[0] if sig.bound else 0,
                lower_bound=sig.bound[1] if sig.bound else 0,
                upper_slice=sig.slice[0] if sig.slice else 0,
                lower_slice=sig.slice[1] if sig.slice else 0,
            )

        data = [sig] if isinstance(sig, str) else sig
        if len(data) == 1:
            bounds = [0, 0, 0, 0]
        elif len(data) == 3:
            bounds = data[1:3] * 2
        else:
            bounds = data[1:]

        [upper_bound, lower_bound, upper_slice, lower_slice] = bounds
        return IPCorePort(
            name=data[0],
            direction=dir,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_slice=upper_slice,
            lower_slice=lower_slice,
        )

    @staticmethod
    def from_port_def(port: LegacyPortDefinition) -> "IPCorePort":
        def _try_int(v: str) -> Union[int, str]:
            try:
                return int(v)
            except ValueError:
                return v

        return IPCorePort(
            name=port.name,
            direction=port.direction,
            upper_bound=_try_int(port.upper_bound),
            lower_bound=_try_int(port.lower_bound),
            upper_slice=_try_int(port.upper_bound),
            lower_slice=_try_int(port.lower_bound),
        )


@marshmallow_dataclass.dataclass(frozen=True)
class IPCorePorts(MarshmallowDataclassExtensions):
    input: Set[Signal] = ext_field(set, data_key="in", inline_depth=1)
    output: Set[Signal] = ext_field(set, data_key="out", inline_depth=1)
    inout: Set[Signal] = ext_field(set, inline_depth=1)

    @cached_property
    def flat(self):
        ports: Set[IPCorePort] = set()
        for dir, sigs in (
            (LegacyPortDirection.IN, self.input),
            (LegacyPortDirection.OUT, self.output),
            (LegacyPortDirection.INOUT, self.inout),
        ):
            for sig in sigs:
                ports.add(IPCorePort.from_sig_and_dir(sig, dir))
        return ports

    @staticmethod
    def from_port_def_list(ports: Collection[LegacyPortDefinition]) -> "IPCorePorts":
        (inp, out, ino) = (set(), set(), set())
        for port in ports:
            (
                inp
                if port.direction == LegacyPortDirection.IN
                else out
                if port.direction == LegacyPortDirection.OUT
                else ino
            ).add(IPCorePort.from_port_def(port).raw)
        return IPCorePorts(input=inp, output=out, inout=ino)


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreIntfPorts(MarshmallowDataclassExtensions):
    input: Dict[str, Optional[Signal]] = ext_field(dict, data_key="in", inline_depth=1)
    output: Dict[str, Optional[Signal]] = ext_field(dict, data_key="out", inline_depth=1)
    inout: Dict[str, Optional[Signal]] = ext_field(dict, inline_depth=1)

    @cached_property
    def flat(self):
        ports: Dict[str, IPCorePort] = {}
        for dir, sigs in (
            (LegacyPortDirection.IN, self.input),
            (LegacyPortDirection.OUT, self.output),
            (LegacyPortDirection.INOUT, self.inout),
        ):
            for iport_name, sig in sigs.items():
                if sig:
                    ports[iport_name] = IPCorePort.from_sig_and_dir(sig, dir)
                else:
                    ports[iport_name] = IPCorePort.from_sig_and_dir(iport_name, dir)
        return ports

    @staticmethod
    def from_port_def_map(ports: Mapping[str, LegacyPortDefinition]) -> "IPCoreIntfPorts":
        (inp, out, ino) = ({}, {}, {})
        for name, port in ports.items():
            (
                inp
                if port.direction == LegacyPortDirection.IN
                else out
                if port.direction == LegacyPortDirection.OUT
                else ino
            )[name] = IPCorePort.from_port_def(port).raw
        return IPCoreIntfPorts(input=inp, output=out, inout=ino)


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreInterface(MarshmallowDataclassExtensions):
    """Interface specified in IP Core YAML file. `Type` field has name of InterfaceDefinition"""

    type: Identifier
    mode: InterfaceModeDescription = ext_field(by_value=True)
    signals: IPCoreIntfPorts = ext_field(IPCoreIntfPorts)
    clock: Optional[str] = ext_field(None)
    reset: Optional[str] = ext_field(None)
    size: Optional[int] = ext_field(None)

    @marshmallow.validates("type")
    def _validate_type(self, id: Identifier) -> bool:
        if get_interface_by_id(id) is None:
            raise marshmallow.ValidationError(f"Invalid interface type: {id.combined()}")
        return True

    @marshmallow.validates_schema
    def _validate(self, self_obj: Dict[str, Any], **kwargs: Any) -> bool:
        if get_config().force_interface_compliance:
            errors: List[str] = []
            iface_def_resource = get_interface_by_id(self_obj["type"])
            if iface_def_resource is None:
                raise ResourceNotFoundException(self_obj["type"].combined())
            i_def = iface_def_resource.definition
            for sig in i_def.signals:
                mode = sig.modes[InterfaceMode.UNSPECIFIED]
                if mode.required:
                    if sig.name not in self_obj["signals"].flat:
                        errors.append(
                            f'Required {mode.direction} port "{sig.name}" of interface'
                            f' "{self_obj["type"]}" not present'
                        )
            for name, sig in self_obj["signals"].flat.items():
                if name not in [s.name for s in i_def.signals]:
                    errors.append(
                        f'Unknown {sig.direction.value} port "{name}", not present in interface'
                        f' "{self_obj["type"].combined()}"'
                    )
            if errors:
                raise marshmallow.ValidationError(errors)
        return True


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreComplexParameter(MarshmallowDataclassExtensions):
    width: int
    value: Union[int, str]


IPCoreParameter = Optional[Union[int, str, IPCoreComplexParameter]]


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreClock(MarshmallowDataclassExtensions):
    signal: str


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreReset(MarshmallowDataclassExtensions):
    signal: str
    polarity: Union[Literal["active low"], Literal["active high"]]
    synchronous_to: Optional[str] = ext_field(None)


class BuiltinIPCoreException(Exception):
    """Raised when an exception occurred during handling a built-in IP Core"""


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreDescription(MarshmallowDataclassExtensions):
    """IP Core as described in YAML IP Core definition file"""

    id: Identifier
    signals: IPCorePorts = ext_field(IPCorePorts)
    parameters: Dict[str, IPCoreParameter] = ext_field(dict)
    interfaces: Dict[str, IPCoreInterface] = ext_field(dict)
    clocks: Dict[str, IPCoreClock] = ext_field(dict)
    resets: Dict[str, IPCoreReset] = ext_field(dict)

    Schema: ClassVar[Type[marshmallow.Schema]]

    def save(self, path: Optional[Path] = None, **kwargs: Any):
        super().save(path if path is not None else Path(self.id.name + ".yaml"), **kwargs)


class IPCoreDescriptionFrontendException(Exception):
    pass


def param_to_ir_param(par: IPCoreParameter) -> Optional[ElaboratableValue]:
    if isinstance(par, IPCoreComplexParameter):
        par = f"{par.width}'d{par.value}"
    return ElaboratableValue(par) if par is not None else None
