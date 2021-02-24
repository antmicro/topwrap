# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from os import listdir, system
from os.path import join, dirname
from yaml import load, Loader

# package-included directories with yamls describing interfaces/IPs
DIR = join(dirname(__file__), 'interfaces')
IP_YAMLS_DIR = join(dirname(__file__), 'ips')


def _default_bounds(signal):
    """Create a default list of bounds for a given signal description
    If no bounds were specified, they default to [0, 0]:
        ['name', 0, 0, 0, 0]
    If no bits of the port were picked, the whole port is picked:
        ['name', x, y, x, y]
    A signal may use a slice of a port
    This example uses the 6th and the 7th bits of the 16-bit port:
        ['example_2_of_16', 15, 0, 7, 6]

    :param signal can be one of:
        'port_name'
        ['port_name', upper_bound, lower_bound]
        ['port_name', upper_bound, lower_bound, upper_picked, lower_picked]

    :return:
        ['port_name', upper_bound, lower_bound, upper_picked, lower_picked]
    """
    # there's just the name
    if isinstance(signal, str):
        return (signal, 0, 0, 0, 0)
    else:
        # there's just the name in a list
        if len(signal) == 1:
            return signal + [0, 0, 0, 0]
        # there's the name and bounds
        if len(signal) == 3:
            return signal + [signal[1], signal[2]]
    return signal


def parse_interface_definitions(dir_name=DIR):
    """Parseinterfaces described in YAML files, bundled with the package

    :param dir_name: directory that contains YAML files for interfaces
    :raises OSError: when dir_name directory cannot be listed
    :return: a list of dicts that represent the yaml files
    """
    try:
        filenames = listdir(dir_name)
    except OSError:
        raise OSError(f"Directory '{dir_name}' "
                      "doesn't exist or cannot be listed")

    defs = []
    for filename in filenames:
        with open(join(dir_name, filename)) as f:
            defs.append(load(f, Loader=Loader))

    return defs


def verilog_to_json(verilog_filename, json_filename):
    """Given filenames of Verilog source and JSON target,
    use 'write_json' function of yosys
    """
    system(f'yosys -p "read_verilog {verilog_filename}" '
           '-p "write_json {json_filename}"')


def parse_port_map(filename: str):
    '''Read a yaml file to gather information about Port <-> Interface mapping.
    This is used for reading per-IP-instance port descriptions.

    :param filename: name of the yaml file. Either in working directory,
        or bundled with the package.
    :return: a dict describing the ports and the interfaces of the IP.
    '''

    try:
        with open(filename) as f:
            ports = load(f, Loader=Loader)

    except FileNotFoundError:
        with open(join(IP_YAMLS_DIR, filename)) as f:
            ports = load(f, Loader=Loader)

    # TODO use this container as a better structure for the data
    # 'signals' : {'in': ..., 'out': ...} generic signals
    # 'interfaces' : {'axi0': ..., 'axis1': ...} signals groupped by interface
    # 'top_module' : name of the top module

    result = dict()
    result['interfaces'] = dict()

    if 'signals' not in ports.keys():
        ports['signals'] = dict()

    # fill non-existent values with defaults
    for key, val in ports.items():
        if key == 'signals':
            try:
                sigs = val['in']
                for i in range(len(sigs)):
                    sigs[i] = _default_bounds(sigs[i])
            except KeyError:  # 'in' doesn't exist in val
                val['in'] = list()
            try:
                sigs = val['out']
                for i in range(len(sigs)):
                    sigs[i] = _default_bounds(sigs[i])
            except KeyError:  # 'out' doesn't exist in val
                val['out'] = list()
            try:
                sigs = val['inout']
                for i in range(len(sigs)):
                    sigs[i] = _default_bounds(sigs[i])
            except KeyError:  # 'inout' doesn't exist in val
                val['inout'] = list()

        else:
            iface = val['signals']
            try:
                sigs = iface['in']
                for key in sigs:
                    sigs[key] = _default_bounds(sigs[key])
            except KeyError:
                iface['in'] = dict()

            try:
                sigs = iface['out']
                for key in sigs:
                    sigs[key] = _default_bounds(sigs[key])
            except KeyError:
                iface['out'] = dict()

            try:
                sigs = iface['inout']
                for key in sigs:
                    sigs[key] = _default_bounds(sigs[key])
            except KeyError:
                iface['inout'] = dict()

    return ports
