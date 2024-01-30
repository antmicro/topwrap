# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from logging import error, info, warning
from os import makedirs, path

from amaranth import Elaboratable, Fragment, Instance, Module, Signal
from amaranth.back import verilog
from amaranth.build import Platform
from amaranth.hdl.ast import Const

from .amaranth_helpers import (
    DIR_IN,
    DIR_INOUT,
    DIR_OUT,
    PortDirection,
    WrapperPort,
    port_direction_to_prefix,
    strip_port_prefix,
)
from .fuse_helper import FuseSocBuilder
from .hierarchy_wrapper import HierarchyWrapper
from .ipwrapper import IPWrapper


class IPConnect(Elaboratable):
    """Connector for multiple IPs, capable of connecting their interfaces
    as well as individual ports.
    """

    def __init__(self):
        self._components = dict()
        self._ports = []

    def add_component(self, name: str, component) -> None:
        """Add a new component to this IPConnect, allowing to make connections with it

        :param name: name of the component
        :param component: IPWrapper or HierarchyWrapper object
        """
        self._components[name] = component
        # create a placeholder for Instance arguments to instantiate the ip
        setattr(self, name, dict())

    def _get_component_by_name(self, name: str):
        try:
            comp = self._components[name]
        except KeyError:
            raise ValueError(
                f"No such IP or hierarchy in this module: {name}."
                " Use add_component() method to add the IP/hierarchy first"
            )
        return comp

    def connect_ports(
        self, port1_name: str, comp1_name: str, port2_name: str, comp2_name: str
    ) -> None:
        """Connect ports of IPs previously added to this Connector

        :param port1_name: name of the port of the 1st IP
        :param comp1_name: name of the 1st IP
        :param port2_name: name of the port of the 2nd IP
        :param comp2_name: name of the 2nd IP
        :raises ValueError: if such IP doesn't exist
        """
        comp1 = self._get_component_by_name(comp1_name)
        comp2 = self._get_component_by_name(comp2_name)
        port1 = comp1.get_port_by_name(port1_name)
        port2 = comp2.get_port_by_name(port2_name)

        if len(port1) != len(port2):
            warning(
                f"ports: {comp1_name}:{port1.name}({len(port1)}), "
                f"{comp2_name}:{port2.name}({len(port2)})"
                " have different widths!"
            )

        if port1.direction == DIR_INOUT or port2.direction == DIR_INOUT:
            warning(
                f"one of {comp1_name}:{port1.name}, {comp2_name}:{port2.name} is inout; "
                "the wire connecting them will be also external in the top module"
            )

        inst1_args = getattr(self, comp1_name)
        inst2_args = getattr(self, comp2_name)

        full_name1 = port_direction_to_prefix(port1.direction) + port1.name
        full_name2 = port_direction_to_prefix(port2.direction) + port2.name

        # If a port was connected previoulsy,
        # take the previoulsy created signal, instead of creating a new one
        if full_name1 in inst1_args.keys():
            sig = inst1_args[full_name1]
        elif full_name2 in inst2_args.keys():
            sig = inst2_args[full_name2]
        else:
            # neither of the ports was connected previously
            # create a new signal for the connection
            combined_name = port1.name + "_" + port2.name
            sig = Signal(len(port1), name=combined_name)

        inst1_args[full_name1] = sig
        inst2_args[full_name2] = sig

    def connect_interfaces(
        self, iface1: str, comp1_name: str, iface2: str, comp2_name: str
    ) -> None:
        """Make connections between all matching ports of the interfaces

        :param iface1: name of the 1st interface
        :param comp1_name: name of the 1st IP
        :param iface2: name of the 2nd interface
        :param comp2_name: name of the 2nd IP
        :raises ValueError: if any of the IPs doesn't exist
        """
        comp1 = self._get_component_by_name(comp1_name)
        comp2 = self._get_component_by_name(comp2_name)
        ip1_ports = comp1.get_ports_of_interface(iface1)
        ip2_ports = comp2.get_ports_of_interface(iface2)

        ip1_signames = {p.name.split("_")[-1] for p in ip1_ports}
        ip2_signames = {p.name.split("_")[-1] for p in ip2_ports}
        ip1_unconnected = ip1_signames - ip2_signames
        ip2_unconnected = ip2_signames - ip1_signames
        if ip1_unconnected:
            info("Unconnected signals of " f"{comp1_name}:{iface1}: {ip1_unconnected}")
        if ip2_unconnected:
            info("Unconnected signals of " f"{comp2_name}:{iface2} {ip2_unconnected}")

        ports_connected = 0
        for p1 in ip1_ports:
            for p2 in ip2_ports:
                names_match = p1.name.split("_")[-1] == p2.name.split("_")[-1]
                # widths_match = len(p1) == len(p2)
                if names_match:
                    self.connect_ports(p1.name, comp1_name, p2.name, comp2_name)
                    ports_connected += 1
        info(
            f"number of ports matched: {ports_connected} for interfaces:"
            f"{comp1_name}:{iface1} - {comp2_name}:{iface2}"
        )

    def _set_port(
        self, comp_name: str, port_name: str, external_name: str, external_dir: PortDirection
    ) -> None:
        """Set port specified by name as an external port

        :param comp_name: name of the component - hierarchy or IP core
        :param port_name: port name in the component
        :param external_name: external name of the port specified in "externals" section
        :param external_dir: external direction of the port specified in "externals" section
        :raises ValueError: if such port doesn't exist
        """
        self._set_unconnected_port(comp_name, port_name, None, external_dir)

        inst_args = getattr(self, comp_name)

        try:
            [name] = list(filter(lambda arg: strip_port_prefix(arg) == port_name, inst_args.keys()))
        except ValueError:  # "not enough"/"too many values" to unpack
            raise ValueError(f'port: "{port_name}" does not exist in ip: ' f"{comp_name}")

        ext_ports = list(filter(lambda port: port.name == external_name, self._ports))
        if len(ext_ports) > 1:
            raise ValueError(f"More than 1 external port named {external_name}")

        # No external port named `external_name` in this IPConnect.
        if not ext_ports:
            sig = inst_args[name]
            sig.name = external_name
            setattr(self, external_name, sig)
            self._ports.append(sig)
            inst_args[name] = getattr(self, external_name)

        # External input port named `external_name` already exists in this IPConnect.
        elif ext_ports[0].direction == DIR_IN:
            inst_args[name] = getattr(self, external_name)

        # External inout or output port named `external_name` already exists in this IPConnect.
        # Raise and error since connections between a single external and many internal ports
        # are allowed for external inputs only.
        else:
            raise ValueError(
                "Multiple connections to external port "
                f"'{external_name}', that is not external input"
            )

    def _set_interface(self, comp_name: str, iface_name: str, external_iface_name: str) -> None:
        """Set interface specified by name as an external interface

        :param comp_name: name of the component - hierarchy or IP core
        :param iface_name: interface name in the component
        :param external_iface_name: external name of the interface specified in "externals" section
        :raises ValueError: if such interface doesn't exist
        """
        comp = self._get_component_by_name(comp_name)

        for port in comp.get_ports_of_interface(iface_name):
            self._set_unconnected_port(comp_name, port.name, external_iface_name, port.direction)

        inst_args = getattr(self, comp_name)

        iface_ports = [
            key for key in inst_args.keys() if strip_port_prefix(key).startswith(iface_name)
        ]
        if not iface_ports:
            raise ValueError(f"no ports exist for interface {iface_name} in ip: {comp_name}")

        for iface_port in iface_ports:
            external_port_name = strip_port_prefix(iface_port).replace(
                iface_name, external_iface_name, 1
            )
            if external_port_name in [port.name for port in self._ports]:
                warning(f"External port '{external_port_name}'" "already exists")
            sig = inst_args[iface_port]
            sig.name = strip_port_prefix(iface_port).replace(iface_name, external_iface_name, 1)
            setattr(self, iface_port, sig)
            self._ports.append(sig)

    def get_ports(self) -> list:
        """Return a list of external ports of this module"""
        return self._ports

    def _set_unconnected_port(
        self, comp_name: str, port_name: str, iface_name: str, external_dir: PortDirection
    ) -> None:
        """Create signal for unconnected port to allow using it as
        external. This is essential since ports that haven't been used have
        no signals assigned to them.
        """
        inst_args = getattr(self, comp_name)
        port = self._get_component_by_name(comp_name).get_port_by_name(port_name)
        full_name = port_direction_to_prefix(port.direction) + port.name

        if full_name not in inst_args.keys():
            inst_args[full_name] = WrapperPort(
                bounds=port.bounds,
                name=full_name,
                internal_name=full_name,
                direction=external_dir,
                interface_name=iface_name,
            )

    def set_constant(self, comp_name: str, comp_port: str, target: int) -> None:
        """Set a constant value on a port of an IP

        :param comp_name: name of the IP or hierarchy
        :param comp_port: name of the port of the IP or hierarchy
        :param target: int value to be assigned
        :raises ValueError: if such IP doesn't exist
        """
        port = self._get_component_by_name(comp_name).get_port_by_name(comp_port)
        inst_args = getattr(self, comp_name)
        full_name = port_direction_to_prefix(port.direction) + port.name
        inst_args[full_name] = Const(target)

    def make_connections(self, ports: dict, interfaces: dict) -> None:
        """Use names of port and names of ips to make connections"""

        for comp1_name, connections in ports.items():
            for comp1_port, target in connections.items():
                # target is one of:
                #   - a number (int)
                #   - an external port name
                #   - list of (comp2_name, comp2_port)
                if isinstance(target, int):
                    self.set_constant(comp1_name, comp1_port, target)
                elif isinstance(target, str):
                    pass
                else:
                    (comp2_name, comp2_port) = target
                    self.connect_ports(comp1_port, comp1_name, comp2_port, comp2_name)

        for comp1_name, connections in interfaces.items():
            for comp1_iface, target in connections.items():
                # target is one of:
                #   - an external interface name
                #   - list of (comp2_name, comp2_iface)
                if isinstance(target, str):
                    pass
                else:
                    (comp2_name, comp2_iface) = target
                    self.connect_interfaces(comp1_iface, comp1_name, comp2_iface, comp2_name)

    def make_external_ports_interfaces(self, ports: dict, interfaces: dict, external: dict) -> None:
        """Pick ports and interfaces which will be used as external I/O"""
        ext_ports = {"in": [], "out": [], "inout": []}
        if "ports" in external.keys():
            for dir in external["ports"].keys():
                ext_ports[dir] = external["ports"][dir]

        for comp_name, connections in ports.items():
            for comp_port, target in connections.items():
                if isinstance(target, str):
                    # check if 'target' is present in the 'externals' section
                    if target in ext_ports["in"]:
                        ext_dir = DIR_IN
                    elif target in ext_ports["out"]:
                        ext_dir = DIR_OUT
                    elif target in ext_ports["inout"]:
                        ext_dir = DIR_INOUT
                    else:
                        raise ValueError(
                            f"External port {target} not found" "in the 'externals' section"
                        )

                    # It is illegal to connect:
                    #  - output to output
                    #  - input to input
                    # Any other connection is legal.
                    port_dir = (
                        self._get_component_by_name(comp_name).get_port_by_name(comp_port).direction
                    )
                    if port_dir != ext_dir and DIR_INOUT not in [port_dir, ext_dir]:
                        raise ValueError(
                            f"Direction of external port '{target}'"
                            f"doesn't match '{comp_name}:{comp_port}' direction"
                        )

                    self._set_port(comp_name, comp_port, target, ext_dir)

        ext_ifaces = []
        if "interfaces" in external.keys():
            for dir in external["interfaces"].keys():
                ext_ifaces += external["interfaces"][dir]

        for comp_name, connections in interfaces.items():
            for comp_iface, target in connections.items():
                if isinstance(target, str):
                    if target not in ext_ifaces:
                        raise ValueError(
                            f"External interface '{target}' not found in 'externals' section"
                        )
                    self._set_interface(comp_name, comp_iface, target)

    def build(
        self,
        build_dir="build",
        template=None,
        sources_dir=None,
        top_module_name="project_top",
        part=None,
    ) -> None:
        # This class is used for generating FuseSoC Core file
        fuse = FuseSocBuilder(part)

        # Identify hierarchies in this IPConenct and build them recursively
        for hier in list(
            filter(lambda comp: isinstance(comp, HierarchyWrapper), self._components.values())
        ):
            hier.ipc.build(top_module_name=hier.name)

        # Identify IPs in this IPConnect and build them
        for ip in list(filter(lambda comp: isinstance(comp, IPWrapper), self._components.values())):
            filename = ip.top_name + ".v"
            fuse.add_source(filename, "verilogSource")

            makedirs(build_dir, exist_ok=True)
            target_file = open(path.join(build_dir, filename), "w")

            fragment = Fragment.get(ip, None)

            output = verilog.convert(fragment, name=ip.top_name, ports=ip.get_ports())
            target_file.write(output)

        fuse.add_source(top_module_name + ".v", "verilogSource")
        fuse.build(path.join(build_dir, "top.core"), sources_dir=sources_dir)
        target_file = open(path.join(build_dir, top_module_name + ".v"), "w")

        fragment = Fragment.get(self, None)
        output = verilog.convert(fragment, name=top_module_name, ports=self.get_ports())
        target_file.write(output)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        for comp_name in self._components.keys():
            args = getattr(self, comp_name)
            try:
                inst = Instance(comp_name, **args)
                setattr(m.submodules, comp_name, inst)
            except TypeError:
                error(f"couldn't create instance of {comp_name} using args: {args}")

        return m
