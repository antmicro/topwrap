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


def generate_design(ips: dict, design: dict, external: dict) -> IPConnect:
    ipc = IPConnect()
    ipc_params = design["parameters"] if "parameters" in design.keys() else dict()
    ipc_ports = design["ports"] if "ports" in design.keys() else dict()
    ipc_interfaces = design["interfaces"] if "interfaces" in design.keys() else dict()

    # Generate hierarchies and add them to `ipc`.
    for key, val in design.items():
        if key not in ["parameters", "ports", "interfaces"]:
            hier_ipc = generate_design(ips, val["design"], val["external"])
            ipc.add_hierarchy(HierarchyWrapper(key, hier_ipc))

    # Find IP cores based on the contents of "ports" and "interfaces" sections
    # and add them to `ipc`.
    hier_names = set(filter(lambda key: key not in ["parameters", "ports", "interfaces"], design.keys()))
    ports_keys, interfaces_keys  = set(ipc_ports.keys()), set(ipc_interfaces.keys())

    for ip_name in ports_keys.union(interfaces_keys).difference(hier_names):
        parameters = ipc_params[ip_name] if ip_name in ipc_params.keys() else dict()
        ipc.add_ip(IPWrapper(ips[ip_name]["file"], ips[ip_name]["module"], ip_name, parameters))

    ipc.make_connections(ipc_ports, ipc_interfaces)
    ipc.make_external_ports_interfaces(ipc_ports, ipc_interfaces, external)
    return ipc


def build_design(design_descr, sources_dir=None, part=None):
    """Build a complete project

    :param design: dict describing the top design
    :param sources_dir: directory to scan to include additional HDL files
        to core file
    """

    design = design_descr["design"] if "design" in design_descr.keys() else dict()
    external = design_descr["external"] if "external" in design_descr.keys() else dict()

    ipc = generate_design(design_descr["ips"], design, external)
    ipc.build(sources_dir=sources_dir, part=part)
