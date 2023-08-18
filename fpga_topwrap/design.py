# Copyright (C) 2021-2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
from yaml import Loader, load

from .ipconnect import IPConnect
from .ipwrapper import IPWrapper


def build_design_from_yaml(yamlfile, sources_dir=None, part=None):
    with open(yamlfile) as f:
        design = load(f, Loader=Loader)
    build_design(design, sources_dir, part)


def generate_design(ips: dict, components: dict, external: dict) -> IPConnect:
    ipc = IPConnect()
    ipc_ports = dict()
    ipc_interfaces = dict()

    for ip_name, ip in components.items():
        if list(ip.keys()) == ["components", "external"]:
            hierarchy = generate_design(ips, ip["components"], ip["external"])
            ipc.add_ip(hierarchy)
        else:
            parameters = dict()
            if "parameters" in ip.keys():
                parameters = ip["parameters"]
            if "ports" in ip.keys():
                ipc_ports[ip_name] = ip["ports"]
            if "interfaces" in ip.keys():
                ipc_interfaces[ip_name] = ip["interfaces"]
            ipc.add_ip(IPWrapper(ips[ip_name]["file"], ips[ip_name]["module"], ip_name, parameters))

    ipc.make_connections(ipc_ports, ipc_interfaces)
    ipc.make_external_ports_interfaces(ipc_ports, ipc_interfaces, external)
    return ipc


def build_design(design, sources_dir=None, part=None):
    """Build a complete project

    :param design: dict describing the top design
    :param sources_dir: directory to scan to include additional HDL files
        to core file
    """

    components = dict()
    external = dict()
    if "components" in design.keys():
        components = design["components"]
    if "external" in design.keys():
        external = design["external"]

    ipc = generate_design(design["ips"], components, external)
    ipc.build(sources_dir=sources_dir, part=part)
