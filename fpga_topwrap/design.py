# Copyright (C) 2021-2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
from yaml import Loader, load

from .ipconnect import IPConnect
from .ipwrapper import IPWrapper


def build_design_from_yaml(yamlfile, sources_dir=None, part=None):
    with open(yamlfile) as f:
        design = load(f, Loader=Loader)
    build_design(design, sources_dir, part)


def build_design(design, sources_dir=None, part=None):
    """Generate a complete project

    :param design: dict describing the top design
    :param sources_dir: directory to scan to include additional HDL files
        to core file
    """
    ipc = IPConnect()

    ports = dict()
    interfaces = dict()
    external = dict()
    if "ports" in design.keys():
        ports = design["ports"]
    if "interfaces" in design.keys():
        interfaces = design["interfaces"]
    if "external" in design.keys():
        external = design["external"]

    for name, ip in design["ips"].items():
        if "parameters" not in ip.keys():
            ip["parameters"] = dict()

        ip_wrapper = IPWrapper(ip["file"], ip["module"], name, ip["parameters"])

        ipc.add_ip(ip_wrapper)

    ipc.make_connections(ports, interfaces)

    ipc.make_external_ports_interfaces(ports, interfaces, external)
    ipc.build(sources_dir=sources_dir, part=part)
