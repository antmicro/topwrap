# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from functools import cached_property, lru_cache
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Collection,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import marshmallow
import marshmallow.validate
import marshmallow_dataclass
from importlib_resources import as_file, files

from topwrap.hdl_parsers_utils import PortDefinition, PortDirection

from .common_serdes import MarshmallowDataclassExtensions, ext_field
from .config import config
from .interface import InterfaceDefinition, InterfaceMode, get_interface_by_name

_T = Union[str, int]

Signal = Union[str, Tuple[str, _T, _T], Tuple[str, _T, _T, _T, _T]]


@marshmallow_dataclass.dataclass(frozen=True)
class IPCorePort:
    name: str
    upper_bound: _T
    lower_bound: _T
    upper_slice: _T
    lower_slice: _T
    direction: PortDirection = ext_field(by_value=True)

    @property
    def bounds(self) -> Tuple[_T, _T, _T, _T]:
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
    def from_sig_and_dir(sig: Signal, dir: PortDirection) -> "IPCorePort":
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
    def from_port_def(port: PortDefinition) -> "IPCorePort":
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
            (PortDirection.IN, self.input),
            (PortDirection.OUT, self.output),
            (PortDirection.INOUT, self.inout),
        ):
            for sig in sigs:
                ports.add(IPCorePort.from_sig_and_dir(sig, dir))
        return ports

    @staticmethod
    def from_port_def_list(ports: Collection[PortDefinition]) -> "IPCorePorts":
        (inp, out, ino) = (set(), set(), set())
        for port in ports:
            (
                inp
                if port.direction == PortDirection.IN
                else out if port.direction == PortDirection.OUT else ino
            ).add(IPCorePort.from_port_def(port).raw)
        return IPCorePorts(input=inp, output=out, inout=ino)


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreIntfPorts(MarshmallowDataclassExtensions):
    input: Dict[str, Signal] = ext_field(dict, data_key="in", deep_cleanup=True, inline_depth=1)
    output: Dict[str, Signal] = ext_field(dict, data_key="out", deep_cleanup=True, inline_depth=1)
    inout: Dict[str, Signal] = ext_field(dict, deep_cleanup=True, inline_depth=1)

    @cached_property
    def flat(self):
        ports: Dict[str, IPCorePort] = {}
        for dir, sigs in (
            (PortDirection.IN, self.input),
            (PortDirection.OUT, self.output),
            (PortDirection.INOUT, self.inout),
        ):
            for iport_name, sig in sigs.items():
                ports[iport_name] = IPCorePort.from_sig_and_dir(sig, dir)
        return ports

    @staticmethod
    def from_port_def_map(ports: Mapping[str, PortDefinition]) -> "IPCoreIntfPorts":
        (inp, out, ino) = ({}, {}, {})
        for name, port in ports.items():
            (
                inp
                if port.direction == PortDirection.IN
                else out if port.direction == PortDirection.OUT else ino
            )[name] = IPCorePort.from_port_def(port).raw
        return IPCoreIntfPorts(input=inp, output=out, inout=ino)


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreInterface(MarshmallowDataclassExtensions):
    type: str
    mode: InterfaceMode = ext_field(by_value=True)
    signals: IPCoreIntfPorts = ext_field(IPCoreIntfPorts)

    @marshmallow.validates("type")
    def _validate_type(self, type: str) -> bool:
        if get_interface_by_name(type) is None:
            raise marshmallow.ValidationError(f"Invalid interface type: {type}")
        return True

    @marshmallow.validates_schema
    def _validate(self, self_obj: Dict[str, Any], **kwargs: Any) -> bool:
        if config.force_interface_compliance:
            errors: List[str] = []
            i_def = cast(InterfaceDefinition, get_interface_by_name(self_obj["type"]))
            for sig in i_def.required_signals:
                if sig.name not in self_obj["signals"].flat:
                    errors.append(
                        f'Required {sig.direction.value} port "{sig.name}" of interface "{self_obj["type"]}" not present'
                    )
            for dir in PortDirection:
                for name in self_obj["signals"].flat:
                    if self_obj["signals"].flat[name].direction == dir and name not in [
                        s.name for s in i_def.signals.flat
                    ]:
                        errors.append(
                            f'Unknown {dir.value} port "{name}", not present in interface "{self_obj["type"]}"'
                        )
            if errors:
                raise marshmallow.ValidationError(errors)
        return True


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreComplexParameter(MarshmallowDataclassExtensions):
    width: int
    value: Union[int, str]


IPCoreParameter = Union[int, str, IPCoreComplexParameter]


class BuiltinIPCoreException(Exception):
    """Raised when an exception occurred during handling a built-in IP Core"""


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreDescription(MarshmallowDataclassExtensions):
    """IP Core as described in YAML IP Core definition file"""

    name: str
    signals: IPCorePorts = ext_field(IPCorePorts)
    parameters: Dict[str, IPCoreParameter] = ext_field(dict, deep_cleanup=True)
    interfaces: Dict[str, IPCoreInterface] = ext_field(dict)

    Schema: ClassVar[Type[marshmallow.Schema]]

    @staticmethod
    @lru_cache(maxsize=None)
    def get_builtins() -> Dict[str, "IPCoreDescription"]:
        """Loads all builtin internal IP Cores

        :return: a dict where keys are the IP Core file names and values are the IP Core description objects
        """

        ips: Dict[str, IPCoreDescription] = {}
        with as_file(files("topwrap.ips")) as ip_res:
            for path in ip_res.glob("**/*.yaml"):
                try:
                    ip = IPCoreDescription.load(path, False)
                    ips[Path(path).stem] = ip
                except Exception as exc:
                    raise BuiltinIPCoreException(
                        f'Loading built-in IP core "{path.name}" failed'
                    ) from exc
        return ips

    @classmethod
    def load(cls, path: Path, fallback: bool = True, **kwargs: Any):
        """Load an IP Core description yaml from the given path

        :param path: the path to the .yaml file
        :param fallback: if this is True and ip_path does not exist, try loading the file from the builtin directory
        :return: the IP Core description object
        """

        try:
            return super().load(path, **kwargs)
        except FileNotFoundError:
            if fallback:
                ips = cls.get_builtins()
                if path.stem in ips:
                    return ips[path.stem]
            raise

    def save(self, path: Optional[Path] = None, **kwargs: Any):
        super().save(path if path is not None else Path(self.name + ".yaml"), **kwargs)
