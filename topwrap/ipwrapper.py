# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from itertools import groupby
from logging import error
from typing import List

import numexpr as ex
from amaranth import Instance, Module, Signal
from amaranth.build import Platform
from amaranth.hdl.ast import Cat, Const

from .amaranth_helpers import (
    DIR_IN,
    DIR_INOUT,
    DIR_OUT,
    WrapperPort,
    port_direction_to_prefix,
)
from .config import config
from .interface import check_interface_compliance, get_interface_by_name
from .parsers import parse_port_map
from .wrapper import Wrapper


def _group_by_internal_name(ports: List[WrapperPort]):
    """Group ports by their 'internal_name' attribute
    return a list of (internal_name, group) where group is a list of ports
    """
    ports.sort(key=lambda x: x.internal_name)
    instances = [(name, list(group)) for name, group in groupby(ports, lambda x: x.internal_name)]
    return instances


def _evaluate_parameters(params: dict):
    """Evaluate parameters values:
    * evaluate params, which values depend on another params
    (e.g. 'param1': 'param2'/2)
    * replace params with 'value' and 'width' with a Const object
    having that specific value and width

    Example:
        'param1': {'value': 10, 'width': 8}
        is replaced with:
        'param1': Const(10, shape=(8))

    :param params: dict of {'name': val} where val is either a number, string
    value, or a dict of {'value': v, 'width': w}, with value `v` of width `w`
    """
    for name in params.keys():
        param = params[name]
        if isinstance(param, Mapping):
            params[name] = Const(param["value"], shape=(param["width"]))
        elif isinstance(param, str):
            if ex.validate(param, params) is None:
                params[name] = int(ex.evaluate(param, params).take(0))


def _eval_bounds(bounds, params):
    """Replace parameter-dependent values with numbers"""
    result = bounds[:]
    for i, item in enumerate(bounds):
        if isinstance(item, str):
            try:
                result[i] = int(ex.evaluate(item, params).take(0))
            except TypeError:
                error(
                    "Could not evaluate expression with parameter: "
                    f'"{item}". Is the parameter defined?'
                )
                raise

    return result


class IPWrapper(Wrapper):
    """This class instantiates an IP in a wrapper to use its individual ports
    or grouped ports as interfaces.
    """

    def __init__(self, yamlfile: str, base_path: str, ip_name: str, instance_name: str, params={}):
        """
        :param yamlfile: name of a file describing
            ports and interfaces of the IP
        :param base_path: path of the project for searching IP description
        :param ip_name: name of the module to wrap
        :param instance_name: name of this instance
        :param params: optional, HDL parameters of this instance
        """
        super().__init__(instance_name)

        self._ports = []
        self._parameters = {}

        _evaluate_parameters(params)
        self._set_parameters(params)

        self.ip_name = ip_name
        self.instance_name = instance_name

        self._create_ports(yamlfile, base_path)

    def _create_ports(self, yamlfile: str, base_path: str):
        """Initialize object attributes with data found in the yamlfile

        :raises ValueError: when interface compliance is violated,
            e.g. the interfaces used don't match the predefined interfaces
        """
        ip_yaml = parse_port_map(yamlfile, base_path)

        parameters = dict()

        if "parameters" in ip_yaml.keys():
            # those are default values of parameters
            parameters = ip_yaml["parameters"]
            _evaluate_parameters(parameters)

        # Overwrite default values with explicit values
        for key, value in self._parameters.items():
            # trim 'p_' in the beginning
            parameters[key[2:]] = value

        signals_dirs = [
            (ip_yaml["signals"]["in"], DIR_IN),
            (ip_yaml["signals"]["out"], DIR_OUT),
            (ip_yaml["signals"]["inout"], DIR_INOUT),
        ]

        # generic signals that don't belong to any interface
        for signals, direction in signals_dirs:
            for port_name, *bounds in signals:
                evaluated_bounds = _eval_bounds(bounds, parameters)
                self._ports.append(
                    WrapperPort(
                        bounds=evaluated_bounds,
                        name=port_name,
                        internal_name=port_name,
                        direction=direction,
                        interface_name=None,
                    )
                )

        for iface_name in ip_yaml["interfaces"].keys():
            iface_signals = ip_yaml["interfaces"][iface_name]["signals"]
            iface_def_name = ip_yaml["interfaces"][iface_name]["type"]
            iface_def = get_interface_by_name(iface_def_name)

            if config.force_interface_compliance:
                if not iface_def:
                    raise ValueError("No such interface definition: " f"{iface_def_name}")

                if not check_interface_compliance(iface_def, iface_signals):
                    raise ValueError(
                        f"Interface: {iface_name} is not "
                        "compliant with interface definition: "
                        f"{iface_def_name}"
                    )

            signals_dirs = [
                (iface_signals["in"].items(), DIR_IN),
                (iface_signals["out"].items(), DIR_OUT),
                (iface_signals["inout"].items(), DIR_INOUT),
            ]

            # sig_name is the name of the signal e.g. TREADY
            for signals, direction in signals_dirs:
                for sig_name, (port_name, *bounds) in signals:
                    external_full_name = iface_name + "_" + sig_name
                    evaluated_bounds = _eval_bounds(bounds, parameters)
                    self._ports.append(
                        WrapperPort(
                            bounds=evaluated_bounds,
                            name=external_full_name,
                            internal_name=port_name,
                            direction=direction,
                            interface_name=iface_name,
                        )
                    )

        # create an attribute for each WrapperPort
        for port in self._ports:
            setattr(self, port.name, port)

    def get_ports(self) -> List[WrapperPort]:
        """Return a list of all ports that belong to this IP."""

        return self._ports

    def _set_parameter(self, name, value):
        self._parameters["p_" + name] = value

    def _set_parameters(self, params: dict):
        """Set parameters defined in HDL source file
            (for example `generic` in VHDL)

        :param params: the names and values of the parameters,
            a dict of {p_name: p_value}
        """
        for key, val in params.items():
            self._set_parameter(key, val)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        instance_args = {}

        for internal_name, ports in _group_by_internal_name(self._ports):
            # Ports must be grouped to allow connecting
            # multiple ports into one, wider port
            #
            # ext_name1[7:6] ---\
            # ext_name2[5:4] ----*-- internal_name[7:0]
            # [fillers]      ---/
            # ext_name3[1:0] ---/

            # Ports must be sorted.
            # The order of concatenation is : Cat(a,b,c) == cba
            ports_sorted = sorted(ports, key=lambda p: p.bounds[2])
            prefix = port_direction_to_prefix(ports_sorted[0].direction)

            # fill the empty slices in the list with Signals
            # the list is iterated starting from last position
            # in order not to change indices
            # or mess up when en element is inserted
            for i in range(len(ports_sorted) - 2, -1, -1):
                port1 = ports_sorted[i]
                port2 = ports_sorted[i + 1]
                if isinstance(port1, WrapperPort) and isinstance(port2, WrapperPort):
                    diff = port2.bounds[3] - port1.bounds[2] - 1
                    if diff > 0:
                        ports_sorted = (
                            ports_sorted[: i + 1] + [Signal(diff)] + ports_sorted[i + 1 :]
                        )

            diff = ports_sorted[0].bounds[3]
            # insert signal in front, if the first doesn't start from 0
            if diff > 0:
                ports_sorted = [Signal(diff)] + ports_sorted

            instance_args[prefix + internal_name] = Cat(*ports_sorted)

        instance_args = {**instance_args, **self._parameters}

        setattr(m.submodules, self.instance_name, Instance(self.ip_name, **instance_args))
        return m
