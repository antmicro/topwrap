# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from os import listdir
from os.path import dirname, join

from yaml import Loader, load

# package-included directories with yamls describing interfaces/IPs
DIR = join(dirname(__file__), "interfaces")
IP_YAMLS_DIR = join(dirname(__file__), "ips")


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
    """Parse interfaces described in YAML files, bundled with the package

    :param dir_name: directory that contains YAML files for interfaces
    :raises OSError: when dir_name directory cannot be listed
    :return: a list of dicts that represent the yaml files
    """
    try:
        filenames = listdir(dir_name)
    except OSError:
        raise OSError(f"Directory '{dir_name}' " "doesn't exist or cannot be listed")

    defs = []
    for filename in filenames:
        with open(join(dir_name, filename)) as f:
            defs.append(load(f, Loader=Loader))

    return defs


def parse_port_map(filename: str, base_path: str = ""):
    """Read a yaml file to gather information about Port <-> Interface mapping.
    This is used for reading per-IP-instance port descriptions.

    :param filename: name of the yaml file. Either in project directory,
        or bundled with the package.
    :param base_path: path of the project with custom IP descriptions
    :return: a dict describing the ports and the interfaces of the IP.
    """
    try:
        with open(join(base_path, filename)) as f:
            ports = load(f, Loader=Loader)

    except FileNotFoundError:
        with open(join(IP_YAMLS_DIR, filename)) as f:
            ports = load(f, Loader=Loader)

    if "signals" not in ports.keys():
        ports["signals"] = dict()
    if "parameters" not in ports.keys():
        ports["parameters"] = dict()
    if "interfaces" not in ports.keys():
        ports["interfaces"] = dict()

    # fill non-existent values with defaults
    sigs_by_dir = ports["signals"]
    for direction in ["in", "out", "inout"]:
        try:
            sigs = sigs_by_dir[direction] or []
            for i in range(len(sigs)):
                sigs[i] = _default_bounds(sigs[i])
            sigs_by_dir[direction] = sigs
        except KeyError:
            sigs_by_dir[direction] = list()

    interfaces = ports["interfaces"] or {}
    for iface_name, iface_def in interfaces.items():
        iface = iface_def["signals"]
        for direction in ["in", "out", "inout"]:
            try:
                sigs = dict()
                for iface_port, rtl_port in iface[direction].items():
                    bounds = _default_bounds(rtl_port)
                    sigs[iface_port] = bounds
                iface[direction] = sigs
            except KeyError:
                iface[direction] = dict()

    result = dict()

    result["parameters"] = ports["parameters"] or {}
    result["signals"] = ports["signals"] or {}
    result["interfaces"] = ports["interfaces"] or {}

    return result
