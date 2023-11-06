# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from logging import error, info, warning
from os import makedirs, path

from amaranth import Elaboratable, Fragment, Instance, Module, Signal
from amaranth.back import verilog
from amaranth.build import Platform
from amaranth.hdl import ClockSignal, ResetSignal
from amaranth.hdl.ast import Const
from soc_generator.gen.wishbone_interconnect import WishboneRRInterconnect

from .amaranth_helpers import (
    DIR_IN,
    DIR_INOUT,
    DIR_OUT,
    PortDirection,
    WrapperPort,
    port_direction_to_prefix,
    strip_port_prefix,
)
from .elaboratable_wrapper import ElaboratableWrapper
from .fuse_helper import FuseSocBuilder
from .ipwrapper import IPWrapper
from .util import removeprefix
from .wrapper import Wrapper


class IPConnect(Wrapper):
    """Connector for multiple IPs, capable of connecting their interfaces
    as well as individual ports.
    """

    def __init__(self, name: str = "ip_connector"):
        super().__init__(name)
        self._components = dict()
        self._ports = []
        self._connections = []

    def add_component(self, name: str, component: Wrapper) -> None:
        """Add a new component to this IPConnect, allowing to make connections with it

        :param name: name of the component
        :param component: Wrapper object
        """
        self._components[name] = component

    def _get_component_by_name(self, name: str):
        try:
            comp = self._components[name]
        except KeyError:
            raise ValueError(
                f"No such IP or hierarchy in this module: {name}."
                " Use add_component() method to add the IP/hierarchy first"
            )
        return comp

    def _connect_internal_ports(self, port1: WrapperPort, port2: WrapperPort):
        """Connects two ports with matching directionality. Disallowed configurations are:
        - input to input
        - output to output
        All other configurations are allowed.

        :param port1: 1st port to connect
        :param port2: 2nd port to connect
        """
        d1, d2 = port1.direction, port2.direction
        if (
            (d1 == DIR_OUT and d2 == DIR_IN)
            or (d1 == DIR_INOUT and d2 == DIR_IN)
            or (d1 == DIR_OUT and d2 == DIR_INOUT)
        ):
            self._connections.append(port2.eq(port1))
        elif (
            (d1 == DIR_IN and d2 == DIR_OUT)
            or (d1 == DIR_IN and d2 == DIR_INOUT)
            or (d1 == DIR_INOUT and d2 == DIR_OUT)
            or (d1 == DIR_INOUT and d2 == DIR_INOUT)
        ):
            # order doesn't matter for inout-inout
            self._connections.append(port1.eq(port2))
        else:
            warning(f"Ports {port1.name} and {port2.name} have mismatched directionality")

    def _connect_external_ports(self, internal: WrapperPort, external: WrapperPort):
        """Makes a pass-through connection - port of an internal module in IPConnect
        is connected to an external IPConnect port.

        :param internal: port of an internal module of IPConnect
        :param external: external IPConnect port
        """
        i, e = internal.direction, external.direction
        if i == DIR_OUT and e == DIR_OUT:
            self._connections.append(external.eq(internal))
        elif i == PortDirection.IN and e == PortDirection.IN:
            self._connections.append(internal.eq(external))
        else:
            # delegate handling inouts
            self._connect_internal_ports(internal, external)

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

        self._connect_internal_ports(port1, port2)

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

        ip1_signames = {removeprefix(p.name, f"{iface1}_") for p in ip1_ports}
        ip2_signames = {removeprefix(p.name, f"{iface2}_") for p in ip2_ports}
        ip1_unconnected = ip1_signames - ip2_signames
        ip2_unconnected = ip2_signames - ip1_signames
        if ip1_unconnected:
            info("Unconnected signals of " f"{comp1_name}:{iface1}: {ip1_unconnected}")
        if ip2_unconnected:
            info("Unconnected signals of " f"{comp2_name}:{iface2}: {ip2_unconnected}")

        ports_connected = 0
        for p1 in ip1_ports:
            for p2 in ip2_ports:
                names_match = removeprefix(p1.name, f"{iface1}_") == removeprefix(
                    p2.name, f"{iface2}_"
                )
                # widths_match = len(p1) == len(p2)
                if names_match:
                    self.connect_ports(p1.name, comp1_name, p2.name, comp2_name)
                    ports_connected += 1
        info(
            f"number of ports matched: {ports_connected} for interfaces:"
            f"{comp1_name}:{iface1} - {comp2_name}:{iface2}"
        )

    def _set_port(self, comp_name: str, port_name: str, external_name: str) -> None:
        """Set port specified by name as an external port

        :param comp_name: name of the component - hierarchy or IP core
        :param port_name: port name in the component
        :param external_name: external name of the port specified in "externals" section
        :raises ValueError: if such port doesn't exist
        """
        comp = self._get_component_by_name(comp_name)

        ports = list(filter(lambda port: port.name == port_name, comp.get_ports()))
        if len(ports) > 1:
            raise ValueError(f"More than 1 port named {port_name} in {comp_name}")
        elif len(ports) == 0:
            raise ValueError(f"Port {port_name} does not exist in ip {comp_name}")
        [port] = ports

        ext_ports = list(filter(lambda port: port.name == external_name, self._ports))
        if len(ext_ports) > 1:
            raise ValueError(f"More than 1 external port named {external_name}")

        # No external port named `external_name` in this IPConnect.
        if not ext_ports:
            external_port = WrapperPort.like(port, name=external_name)
            self._ports.append(external_port)
            self._connect_external_ports(port, external_port)
        # External input port named `external_name` already exists in this IPConnect.
        elif ext_ports[0].direction == DIR_IN:
            self._connect_external_ports(port, ext_ports[0])
        # External inout or output port named `external_name` already exists in this IPConnect.
        # Raise an error since connections between a single external and many internal ports
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

        iface_ports = [port for port in comp.get_ports() if port.interface_name == iface_name]
        if not iface_ports:
            raise ValueError(f"no ports exist for interface {iface_name} in ip: {comp_name}")

        for iface_port in iface_ports:
            external_port = WrapperPort.like(iface_port)
            external_port.name = external_port.name.replace(iface_name, external_iface_name, 1)
            external_port.interface_name = external_iface_name
            if external_port.name in [port.name for port in self._ports]:
                warning(f"External port '{external_port.name}'" "already exists")

            self._connect_external_ports(iface_port, external_port)
            self._ports.append(external_port)

    def get_ports(self) -> list:
        """Return a list of external ports of this module"""
        return self._ports

    def set_constant(self, comp_name: str, comp_port: str, target: int) -> None:
        """Set a constant value on a port of an IP

        :param comp_name: name of the IP or hierarchy
        :param comp_port: name of the port of the IP or hierarchy
        :param target: int value to be assigned
        :raises ValueError: if such IP doesn't exist
        """
        port = self._get_component_by_name(comp_name).get_port_by_name(comp_port)
        self._connections.append(port.eq(Const(target)))

    def make_connections(self, ports: dict, interfaces: dict, interconnects: dict) -> None:
        """Use names of port and names of ips to make connections"""

        for ic_name, params in interconnects.items():
            ic = self._get_component_by_name(ic_name)

            masters, slaves = params["masters"], params["slaves"]

            for slave_name, slave_ifaces in slaves.items():
                for slave_iface_name, iface_params in slave_ifaces.items():
                    address, size = iface_params["address"], iface_params["size"]
                    ic.elaboratable.add_peripheral(
                        name=f"{slave_name}_{slave_iface_name}", addr=address, size=size
                    )

            for master_name, master_ifaces in masters.items():
                for master_iface_name in master_ifaces:
                    ic.elaboratable.add_master(name=f"{master_name}_{master_iface_name}")

            for slave_name, slave_ifaces in slaves.items():
                for slave_iface_name, iface_params in slave_ifaces.items():
                    self.connect_interfaces(
                        slave_iface_name, slave_name, f"{slave_name}_{slave_iface_name}", ic_name
                    )

            for master_name, master_ifaces in masters.items():
                for master_iface_name in master_ifaces:
                    self.connect_interfaces(
                        master_iface_name,
                        master_name,
                        f"{master_name}_{master_iface_name}",
                        ic_name,
                    )

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

                    self._set_port(comp_name, comp_port, target)

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

        fuse.add_source(top_module_name + ".v", "verilogSource")
        fuse.build(path.join(build_dir, "top.core"), sources_dir=sources_dir)
        target_file = open(path.join(build_dir, top_module_name + ".v"), "w")

        fragment = Fragment.get(self, None)
        output = verilog.convert(fragment, name=top_module_name, ports=self.get_ports())
        target_file.write(output)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        # self._connections only contains Amaranth assignment objects, to truly
        # create the connections we have to add them to the comb domain
        m.d.comb += self._connections

        for comp_name, comp in self._components.items():
            setattr(m.submodules, comp_name, comp)

        return m
