# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from yaml import load, Loader
from collections.abc import Mapping
from nmigen.hdl.ast import Const
from .ipconnect import IPConnect
from .ipwrapper import IPWrapper


def _interpret_parameters(params):
    """Replace params with 'value' and 'width' with a Const object
    having that specific value and width

    Example:
        'param1': {'value': 10, 'width': 8}
        is replaced with:
        'param1': Const(10, shape=(8))

    :param params: dict of {'name': val} where val is either a the value,
        or a dict of {'value': v, 'width': w}, with value `v` of width `w`
    """
    for name in params.keys():
        param = params[name]
        if isinstance(param, Mapping):
            params[name] = Const(param['value'], shape=(param['width']))


def build_design(yamlfile, sources_dir=None):
    """Generate a complete project

    :param yamlfile: file describing the top design
    :param sources_dir: directory to scan to include additional HDL files
        to core file
    """
    ipc = IPConnect()

    with open(yamlfile) as f:
        design = load(f, Loader=Loader)

    ports = dict()
    interfaces = dict()
    external = dict()
    if 'ports' in design.keys():
        ports = design['ports']
    if 'interfaces' in design.keys():
        interfaces = design['interfaces']
    if 'external' in design.keys():
        external = design['external']

    for name, ip in design['ips'].items():
        ip_wrapper = IPWrapper(ip['file'],
                               ip['module'],
                               name)
        if 'parameters' in ip.keys():
            _interpret_parameters(ip['parameters'])
            ip_wrapper.set_parameters(ip['parameters'])

        ipc.add_ip(ip_wrapper)

    ipc.make_connections(ports, interfaces)

    ipc.make_external_ports(external)
    ipc.build(sources_dir=sources_dir)
