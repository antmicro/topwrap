# Copyright (C) 2021-2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
from yaml import Loader, load

from .ipconnect import IPConnect
from .ipwrapper import IPWrapper
from .hierarchy_wrapper import HierarchyWrapper


def build_design_from_yaml(yamlfile, sources_dir=None, part=None):
    with open(yamlfile) as f:
        design = load(f, Loader=Loader)
    build_design(design, sources_dir, part)


def generate_design(ips: dict, components: dict, external: dict) -> IPConnect:
    ipc = IPConnect()
    ipc_ports = dict()
    ipc_interfaces = dict()

    for comp_name, comp in components.items():
        if list(comp.keys()) == ["components", "external"]:
            hier_ipc = generate_design(ips, comp["components"], comp["external"])
            ipc.add_hierarchy(HierarchyWrapper(comp_name, hier_ipc))
        else:
            parameters = dict()
            if "parameters" in comp.keys():
                parameters = comp["parameters"]
            if "ports" in comp.keys():
                ipc_ports[comp_name] = comp["ports"]
            if "interfaces" in comp.keys():
                ipc_interfaces[comp_name] = comp["interfaces"]
            ipc.add_ip(IPWrapper(ips[comp_name]["file"], ips[comp_name]["module"], comp_name, parameters))

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
