# amaranth: UnusedElaboratable=no

# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from logging import error
from pathlib import Path

from soc_generator.gen.wishbone_interconnect import WishboneRRInterconnect
from yaml import Loader, load

from .elaboratable_wrapper import ElaboratableWrapper
from .ipconnect import IPConnect
from .ipwrapper import IPWrapper


def build_design_from_yaml(yamlfile, build_dir, sources_dir=None, part=None):
    with open(yamlfile) as f:
        design = load(f, Loader=Loader)
    build_design(design, build_dir, sources_dir, part)


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

    interconnects = (
        design_descr["interconnects"] if "interconnects" in design_descr.keys() else dict()
    )
    interconnect_conns = set()
    for interconnect in interconnects.values():
        if "slaves" in interconnect.keys():
            interconnect_conns |= interconnect["slaves"].keys()
        if "masters" in interconnect.keys():
            interconnect_conns |= interconnect["masters"].keys()

    # IP core should be added to the design if its name occurs as a key in "ports",
    # "interfaces" or "interconnects.<interconnect_name>.{slaves, masters}" sections
    # of a design description yaml (and it is not a hierarchy name).
    return (ports_keys | interfaces_keys | interconnect_conns) - get_hierarchies_names(design_descr)


def get_interconnects_names(design_descr: dict) -> set:
    """Returns a set of interconnect names present in design description YAML"""
    return (
        set(design_descr["interconnects"].keys())
        if "interconnects" in design_descr.keys()
        else set()
    )


def generate_design(ips: dict, design: dict, external: dict) -> IPConnect:
    ipc = IPConnect()
    ipc_params = design["parameters"] if "parameters" in design.keys() else dict()
    ipc_hiers = design["hierarchies"] if "hierarchies" in design.keys() else dict()
    ipc_ports = design["ports"] if "ports" in design.keys() else dict()
    ipc_interfaces = design["interfaces"] if "interfaces" in design.keys() else dict()
    ipc_interconnects = design["interconnects"] if "interconnects" in design.keys() else dict()
    ipc_inouts = external["ports"]["inout"] if "inout" in external["ports"].keys() else dict()

    # Generate hierarchies and add them to `ipc`.
    for hier_name in get_hierarchies_names(design):
        hier_ipc = generate_design(
            ips, ipc_hiers[hier_name]["design"], ipc_hiers[hier_name]["external"]
        )
        ipc.add_component(hier_name, hier_ipc)

    for ip_name in get_ipcores_names(design):
        ip_file = ips[ip_name]["file"]
        ip_module = ips[ip_name]["module"]
        ip_params = ipc_params[ip_name] if ip_name in ipc_params.keys() else dict()
        ipc.add_component(ip_name, IPWrapper(ip_file, ip_module, ip_name, ip_params))

    for interconnect_name in get_interconnects_names(design):
        ic = ipc_interconnects[interconnect_name]
        ic_type = ic["type"]
        ic_cls = {
            "wishbone_roundrobin": WishboneRRInterconnect,
            # place for more interconnect name: class mappings
        }[ic_type]
        ic_params = ic["params"]  # interconnect-dependent parameters
        ipc.add_component(
            interconnect_name,
            ElaboratableWrapper(
                name=interconnect_name,
                elaboratable=ic_cls(**ic_params),
            ),
        )

    ipc.make_connections(ipc_ports, ipc_interfaces, external)
    ipc.make_interconnect_connections(ipc_interconnects, external)
    ipc.validate_inout_connections(ipc_inouts)
    return ipc


def build_design(design_descr, build_dir, sources_dir=None, part=None):
    """Build a complete project

    :param design: dict describing the top design
    :param sources_dir: directory to scan to include additional HDL files
        to core file
    """

    design = design_descr["design"] if "design" in design_descr.keys() else dict()
    external = design_descr["external"] if "external" in design_descr.keys() else dict()

    design_name = design["name"] if "name" in design else "top"
    build_path = Path(build_dir)

    try:
        build_path.mkdir(exist_ok=True)
    except (FileExistsError, FileNotFoundError) as e:
        # raised when path already exists but is not a directory or when parent directory is missing
        error(e)
        return

    ipc = generate_design(design_descr["ips"], design, external)
    ipc.build(build_dir=build_dir, sources_dir=sources_dir, part=part, top_module_name=design_name)
