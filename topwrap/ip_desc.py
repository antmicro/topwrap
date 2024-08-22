# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from dataclasses import field
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
import yaml
from importlib_resources import as_file, files

from topwrap.hdl_parsers_utils import PortDefinition, PortDirection

from .common_serdes import optional_with
from .config import config
from .interface import InterfaceDefinition, InterfaceMode, get_interface_by_name

_T = Union[str, int]

Signal = Union[str, Tuple[str], Tuple[str, _T, _T], Tuple[str, _T, _T, _T, _T]]


@marshmallow_dataclass.dataclass(frozen=True)
class IPCorePort:
    name: str
    upper_bound: _T
    lower_bound: _T
    upper_slice: _T
    lower_slice: _T
    direction: PortDirection = field(metadata={"by_value": True})

    @property
    def bounds(self) -> Tuple[_T, _T, _T, _T]:
        return (self.upper_bound, self.lower_bound, self.upper_slice, self.lower_slice)

    @cached_property
    def raw(self) -> Signal:
        tdb = self.bounds
        if tdb == (0, 0, 0, 0):
            tdb = ()
        elif tdb[:2] == tdb[2:]:
            tdb = tdb[:2]
        return (self.name, *tdb)

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
class IPCorePorts:
    input: Set[Signal] = optional_with(set, {"data_key": "in"})
    output: Set[Signal] = optional_with(set, {"data_key": "out"})
    inout: Set[Signal] = optional_with(set)

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
                else out
                if port.direction == PortDirection.OUT
                else ino
            ).add(IPCorePort.from_port_def(port).raw)
        return IPCorePorts(input=inp, output=out, inout=ino)


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreIntfPorts:
    input: Dict[str, Signal] = optional_with(dict, {"data_key": "in"})
    output: Dict[str, Signal] = optional_with(dict, {"data_key": "out"})
    inout: Dict[str, Signal] = optional_with(dict)

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
                else out
                if port.direction == PortDirection.OUT
                else ino
            )[name] = IPCorePort.from_port_def(port).raw
        return IPCoreIntfPorts(input=inp, output=out, inout=ino)


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreInterface:
    type: str
    mode: InterfaceMode = field(metadata={"by_value": True})
    signals: IPCoreIntfPorts = optional_with(IPCoreIntfPorts)

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
class IPCoreComplexParameter:
    width: int
    value: Union[int, str]


IPCoreParameter = Union[int, str, IPCoreComplexParameter]


class BuiltinIPCoreException(Exception):
    """Raised when an exception occurred during handling a built-in IP Core"""


@marshmallow_dataclass.dataclass(frozen=True)
class IPCoreDescription:
    """IP Core as described in YAML IP Core definition file"""

    name: str
    signals: IPCorePorts = optional_with(IPCorePorts)
    parameters: Dict[str, IPCoreParameter] = optional_with(dict)
    interfaces: Dict[str, IPCoreInterface] = optional_with(dict)

    Schema: ClassVar[Type[marshmallow.Schema]]

    @staticmethod
    @lru_cache(maxsize=None)
    def get_builtins() -> Dict[str, "IPCoreDescription"]:
        """Loads all builtin internal IP Cores

        :return: a dict where keys are the IP Core names and values are the IP Core description objects
        """

        ips: Dict[str, IPCoreDescription] = {}
        with as_file(files("topwrap.ips")) as ip_res:
            for path in ip_res.glob("**/*"):
                if path.suffix.lower() in (".yaml", ".yml"):
                    try:
                        ip = IPCoreDescription.load(path, False)
                        ips[ip.name] = ip
                    except Exception as exc:
                        raise BuiltinIPCoreException(
                            f'Loading built-in IP core "{path.name}" failed'
                        ) from exc
        return ips

    @staticmethod
    @lru_cache(maxsize=None)
    def get_builtins_by_file() -> Dict[str, "IPCoreDescription"]:
        """Loads all builtin internal IP Cores

        :return: a dict where keys are IP Core file names and values are IP Core definition objects
        """
        # this is needed for when loading builtin by file name not by module name

        ips: Dict[str, IPCoreDescription] = {}
        with as_file(files("topwrap.ips")) as ip_res:
            for path in ip_res.glob("**/*"):
                if path.suffix.lower() in (".yaml", ".yml"):
                    try:
                        ip = IPCoreDescription.load(path, False)
                        ips[Path(path).stem] = ip
                    except Exception as exc:
                        raise BuiltinIPCoreException(
                            f'Loading built-in IP core "{path.name}" failed'
                        ) from exc
        return ips

    @staticmethod
    def load(ip_path: Union[str, Path], fallback: bool = True) -> "IPCoreDescription":
        """Load an IP Core description yaml from the given path

        :param ip_path: the path to the .yaml file
        :param fallback: if this is True and ip_path does not exist, try loading the file from the builtin directory
        :return: the IP Core description object
        """

        ip_path = Path(ip_path)

        try:
            with open(ip_path) as f:
                return cast(IPCoreDescription, IPCoreDescription.Schema().load(yaml.safe_load(f)))
        except FileNotFoundError:
            if fallback:
                ips = IPCoreDescription.get_builtins()
                if ip_path.stem in ips:
                    return ips[ip_path.stem]
                ips = IPCoreDescription.get_builtins_by_file()
                if ip_path.stem in ips:
                    return ips[ip_path.stem]
            raise

    def save(self, file_path: Optional[Union[str, Path]] = None):
        if file_path is None:
            file_path = self.name + ".yaml"

        with open(file_path, "w") as f:
            yaml.safe_dump(self.Schema().dump(self), f, sort_keys=False)
