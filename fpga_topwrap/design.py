# amaranth: UnusedElaboratable=no

# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from yaml import Loader, load

from .hierarchy_wrapper import HierarchyWrapper
from .ipconnect import IPConnect
from .ipwrapper import IPWrapper


def build_design_from_yaml(yamlfile, sources_dir=None, part=None):
    with open(yamlfile) as f:
        design = load(f, Loader=Loader)
    build_design(design, sources_dir, part)


def get_hierarchies_names(design_descr: dict) -> set:
    """`design_descr` is the "design" section of a design description yaml."""
    if "hierarchies" not in design_descr.keys():
        return set()
    return set(design_descr["hierarchies"].keys())


def get_ipcores_names(design_descr: dict) -> set:
    """`design_descr` is the "design" section of a design description yaml."""
    design_ports = design_descr["ports"] if "ports" in design_descr.keys() else dict()
    design_interfaces = (
        design_descr["interfaces"] if "interfaces" in design_descr.keys() else dict()
    )
    ports_keys = set(design_ports.keys())
    interfaces_keys = set(design_interfaces.keys())
    # IP core should be added to the design if its name occurs as a key in "ports" or
    # "interfaces" sections of a design description yaml (and it is not a hierarchy name).
    return ports_keys.union(interfaces_keys).difference(get_hierarchies_names(design_descr))


def generate_design(ips: dict, design: dict, external: dict) -> IPConnect:
    ipc = IPConnect()
    ipc_params = design["parameters"] if "parameters" in design.keys() else dict()
    ipc_hiers = design["hierarchies"] if "hierarchies" in design.keys() else dict()
    ipc_ports = design["ports"] if "ports" in design.keys() else dict()
    ipc_interfaces = design["interfaces"] if "interfaces" in design.keys() else dict()

    # Generate hierarchies and add them to `ipc`.
    for hier_name in get_hierarchies_names(design):
        hier_ipc = generate_design(
            ips, ipc_hiers[hier_name]["design"], ipc_hiers[hier_name]["external"]
        )
        ipc.add_component(hier_name, HierarchyWrapper(hier_name, hier_ipc))

    for ip_name in get_ipcores_names(design):
        ip_file = ips[ip_name]["file"]
        ip_module = ips[ip_name]["module"]
        ip_params = ipc_params[ip_name] if ip_name in ipc_params.keys() else dict()
        ipc.add_component(ip_name, IPWrapper(ip_file, ip_module, ip_name, ip_params))

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
