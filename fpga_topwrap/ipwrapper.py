# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from typing import List
from itertools import groupby
from collections.abc import Mapping
from logging import error
import numexpr as ex
from amaranth import Elaboratable, Module, Instance, Signal
from amaranth.build import Platform
from amaranth.hdl.rec import DIR_FANIN, DIR_FANOUT, DIR_NONE
from amaranth.hdl.ast import Cat, Const
from .parsers import parse_port_map
from .nm_helper import WrapperPort, port_direction_to_prefix
from .interface import get_interface_by_name
from .config import config
from .util import check_interface_compliance


def _group_by_internal_name(ports: List[WrapperPort]):
    """Group ports by their 'internal_name' attribute
    return a list of (internal_name, group) where group is a list of ports
    """
    ports.sort(key=lambda x: x.internal_name)
    instances = [(name, list(group)) for name, group
                 in groupby(ports, lambda x: x.internal_name)]
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
            params[name] = Const(param['value'], shape=(param['width']))
        elif isinstance(param, str):
            params[name] = int(ex.evaluate(params[name], params).take(0))


def _eval_bounds(bounds, params):
    """Replace parameter-dependent values with numbers"""
    result = bounds[:]
    for i, item in enumerate(bounds):
        if isinstance(item, str):
            try:
                result[i] = int(ex.evaluate(item, params).take(0))
            except TypeError:
                error('Could not evaluate expression with parameter: '
                      f'"{item}". Is the parameter defined?')
                raise

    return result


class IPWrapper(Elaboratable):
    '''This class instantiates an IP in a wrapper to use its individual ports
    or groupped ports as interfaces.
    '''

    def __init__(self, yamlfile: str, ip_name: str, top_name, params={}):
        '''
        :param yamlfile: name of a file describing
            ports and interfaces of the IP
        :param ip_name: name of the module to wrap
        :param top_name: the name of the top wrapper module,
            defaults to ip_name + '_top'
        :param params: HDL parameters of this instance
        '''
        self._ports = []
        self._parameters = {}

        _evaluate_parameters(params)
        self.set_parameters(params)

        self._create_ports(yamlfile)
        self.ip_name = ip_name

        if top_name is None:
            self.top_name = ip_name + '_top'
        else:
            self.top_name = top_name

    def _create_ports(self, yamlfile: str):
        """Initialize object attributes with data found in the yamlfile

        :raises ValueError: when interface compliance is violated,
            e.g. the interfaces used don't match the predefined interfaces
        """
        ip_yaml = parse_port_map(yamlfile)

        parameters = dict()

        if 'parameters' in ip_yaml.keys():
            # those are default values of parameters
            parameters = ip_yaml['parameters']
            _evaluate_parameters(parameters)
            del ip_yaml['parameters']

        # Overwrite default values with explicit values
        for key, value in self._parameters.items():
            # trim 'p_' in the beginning
            parameters[key[2:]] = value

        # generic signals that don't belong to any interface
        for port_name, *bounds in ip_yaml['signals']['in']:
            evaluated_bounds = _eval_bounds(bounds, parameters)
            self._ports.append(
                    WrapperPort(bounds=evaluated_bounds,
                                name=port_name,
                                internal_name=port_name,
                                direction=DIR_FANIN,
                                interface_name='None')
                    )

        for port_name, *bounds in ip_yaml['signals']['out']:
            evaluated_bounds = _eval_bounds(bounds, parameters)
            self._ports.append(
                    WrapperPort(bounds=evaluated_bounds,
                                name=port_name,
                                internal_name=port_name,
                                direction=DIR_FANOUT,
                                interface_name='None')
                    )

        for port_name, *bounds in ip_yaml['signals']['inout']:
            evaluated_bounds = _eval_bounds(bounds, parameters)
            self._ports.append(
                    WrapperPort(bounds=evaluated_bounds,
                                name=port_name,
                                internal_name=port_name,
                                direction=DIR_NONE,
                                interface_name='None')
                    )

        # get rid of those generic signals to handle all the rest
        # all the other keys represent interface names
        del ip_yaml['signals']

        for iface_name in ip_yaml.keys():
            signals = ip_yaml[iface_name]['signals']
            ins = signals['in'].items()
            outs = signals['out'].items()
            inouts = signals['inout'].items()
            iface_def_name = ip_yaml[iface_name]['interface']
            iface_def = get_interface_by_name(iface_def_name)

            if config.force_interface_compliance:
                if not iface_def:
                    raise ValueError('No such interface definition: '
                                     f'{iface_def_name}')

                if not check_interface_compliance(iface_def, signals):
                    raise ValueError(f'Interface: {iface_name} is not '
                                     'compliant with interface definition: '
                                     f'{iface_def_name}')

            # sig_name is the name of the signal e.g. TREADY
            for sig_name, (port_name, *bounds) in ins:
                external_full_name = iface_name + '_' + sig_name
                evaluated_bounds = _eval_bounds(bounds, parameters)
                self._ports.append(
                        WrapperPort(bounds=evaluated_bounds,
                                    name=external_full_name,
                                    internal_name=port_name,
                                    direction=DIR_FANIN,
                                    interface_name=iface_name)
                        )

            for sig_name, (port_name, *bounds) in outs:
                external_full_name = iface_name + '_' + sig_name
                evaluated_bounds = _eval_bounds(bounds, parameters)
                self._ports.append(
                        WrapperPort(bounds=evaluated_bounds,
                                    name=external_full_name,
                                    internal_name=port_name,
                                    direction=DIR_FANOUT,
                                    interface_name=iface_name)
                        )

            for sig_name, (port_name, *bounds) in inouts:
                external_full_name = iface_name + '_' + sig_name
                evaluated_bounds = _eval_bounds(bounds, parameters)
                self._ports.append(
                        WrapperPort(bounds=evaluated_bounds,
                                    name=external_full_name,
                                    internal_name=port_name,
                                    direction=DIR_NONE,
                                    interface_name=iface_name)
                        )

        # create an attribute for each WrapperPort
        for port in self._ports:
            setattr(self, port.name, port)

    def get_ports(self) -> List[WrapperPort]:
        """Return a list of all ports that belong to this IP.
        """

        return self._ports

    def get_ports_of_interface(self, iface_name: str) -> List[WrapperPort]:
        """Return a list of ports of specific interface.

        :raises ValueError: if such interface doesn't exist.
        """
        ports = [port for port in
                 filter(lambda x: x.interface_name == iface_name, self._ports)
                 ]
        if not ports:
            raise ValueError('No ports could be found for '
                             f'this interface name: {iface_name}')
        return ports

    def get_port_by_name(self, name: str) -> WrapperPort:
        """Given port's name, return the port as WrapperPort object.

        :raises ValueError: If such port doesn't exist.
        """
        try:
            port = getattr(self, name)
        except AttributeError:
            raise ValueError(f"Port named '{name}' couldn't be found"
                             f" in the IP: {self.ip_name}")
        return port

    def get_port_names(self) -> List[str]:
        """Return a list of names of all ports of this IP.
        """
        return [port.name for port in self._ports]

    def get_port_names_of_interface(self, iface_name: str) -> List[str]:
        """Return a list of names of ports that belong to specific interface.
        """
        names = [port.name for port in self.get_ports_of_interface(iface_name)]
        return names

    def _set_parameter(self, name, value):
        self._parameters['p_' + name] = value

    def set_parameters(self, params: dict):
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
            # Ports must be groupped to allow connecting
            # multiple ports into one, wider port
            #
            # ext_name1[7:6] ---\
            # ext_name2[5:4] ----*-- internal_name[7:0]
            # [fillers]      ---/
            # ext_name3[1:0] ---/

            # Ports must be sorted.
            # The order of concatentation is : Cat(a,b,c) == cba
            ports_sorted = sorted(ports, key=lambda p: p.bounds[2])
            prefix = port_direction_to_prefix(ports_sorted[0].direction)

            # fill the empty slices in the list with Signals
            # the list is iterated starting from last position
            # in order not to change indices
            # or mess up when en alement is inserted
            for i in range(len(ports_sorted)-2, -1, -1):
                port1 = ports_sorted[i]
                port2 = ports_sorted[i+1]
                if (isinstance(port1, WrapperPort)
                        and isinstance(port2, WrapperPort)):
                    diff = port2.bounds[3] - port1.bounds[2] - 1
                    if diff > 0:
                        ports_sorted = (ports_sorted[:i+1]
                                        + [Signal(diff)]
                                        + ports_sorted[i+1:])

            diff = ports_sorted[0].bounds[3]
            # insert signal in front, if the first doesn't start from 0
            if diff > 0:
                ports_sorted = [Signal(diff)] + ports_sorted

            instance_args[prefix + internal_name] = Cat(*ports_sorted)

        instance_args = {**instance_args, **self._parameters}

        m.submodules.ip = Instance(self.ip_name, **instance_args)
        return m
