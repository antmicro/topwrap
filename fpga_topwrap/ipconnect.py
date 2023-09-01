# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import error, info, warning
from os import makedirs, path

from amaranth import Elaboratable, Fragment, Instance, Module, Signal
from amaranth.back import verilog
from amaranth.build import Platform
from amaranth.hdl.ast import Const

from .fuse_helper import FuseSocBuilder
from .ipwrapper import IPWrapper
from .nm_helper import port_direction_to_prefix, strip_port_prefix, DIR_IN, DIR_OUT, DIR_INOUT, PortDirection


class IPConnect(Elaboratable):
    """Connector for multiple IPs, capable of connecting their interfaces
    as well as individual ports.
    """

    def __init__(self):
        self._signals_between_ips = []
        self._ips = dict()
        self._ips_by_internal_name = dict()
        self._ports = []

    def add_ip(self, ip: IPWrapper) -> None:
        """Add a new IPWrapper object, allowing to make connections with it"""
        ip_name = ip.top_name
        self._ips[ip_name] = ip
        self._ips_by_internal_name[ip.ip_name] = ip
        # create a placeholder for Instance arguments to instantiate the ip
        setattr(self, ip_name, dict())

    def connect_ports(self, port1_name: str, ip1_name: str, port2_name: str, ip2_name: str) -> None:
        """Connect ports of IPs previously added to this Connector

        :param port1_name: name of the port of the 1st IP
        :param ip1_name: name of the 1st IP
        :param port2_name: name of the port of the 2nd IP
        :param ip2_name: name of the 2nd IP
        :raises ValueError: if such IP doesn't exist
        """
        if ip1_name not in self._ips.keys() or ip2_name not in self._ips.keys():
            raise ValueError(
                f"No such IP in this module: {ip1_name}, {ip2_name}."
                " Use add_ip method to add the IPs first"
            )
        # get the 'WrapperPort's
        port1 = self._ips[ip1_name].get_port_by_name(port1_name)
        port2 = self._ips[ip2_name].get_port_by_name(port2_name)

        if len(port1) != len(port2):
            warning(
                f"ports: {ip1_name}:{port1.name}({len(port1)}), "
                f"{ip2_name}:{port2.name}({len(port2)})"
                " have different widths!"
            )

        if port1.direction == DIR_INOUT or port2.direction == DIR_INOUT:
            warning(
                f"one of {ip1_name}:{port1.name}, {ip2_name}:{port2.name} is inout; "
                "the wire connecting them will be also external in the top module"
            )

        inst1_args = getattr(self, ip1_name)
        inst2_args = getattr(self, ip2_name)

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
            self._signals_between_ips.append(combined_name)
            sig = Signal(len(port1), name=combined_name)
            setattr(self, combined_name, sig)

        inst1_args[full_name1] = sig
        inst2_args[full_name2] = sig

    def connect_interfaces(self, iface1: str, ip1_name: str, iface2: str, ip2_name: str) -> None:
        """Make connections between all matching ports of the interfaces

        :param iface1: name of the 1st interface
        :param ip1_name: name of the 1st IP
        :param iface2: name of the 2nd interface
        :param ip2_name: name of the 2nd IP
        :raises ValueError: if any of the IPs doesn't exist
        """
        if ip1_name not in self._ips.keys() or ip2_name not in self._ips.keys():
            raise ValueError(
                f"No such IP in this module: {ip1_name}, {ip2_name}."
                " Use add_ip method to add the IPs first"
            )

        ip1_ports = self._ips[ip1_name].get_ports_of_interface(iface1)
        ip2_ports = self._ips[ip2_name].get_ports_of_interface(iface2)

        ip1_signames = {p.name.split("_")[-1] for p in ip1_ports}
        ip2_signames = {p.name.split("_")[-1] for p in ip2_ports}
        ip1_unconnected = ip1_signames - ip2_signames
        ip2_unconnected = ip2_signames - ip1_signames
        if ip1_unconnected:
            info("Unconnected signals of " f"{ip1_name}:{iface1}: {ip1_unconnected}")
        if ip2_unconnected:
            info("Unconnected signals of " f"{ip2_name}:{iface2} {ip2_unconnected}")

        ports_connected = 0
        for p1 in ip1_ports:
            for p2 in ip2_ports:
                names_match = p1.name.split("_")[-1] == p2.name.split("_")[-1]
                # widths_match = len(p1) == len(p2)
                if names_match:
                    self.connect_ports(p1.name, ip1_name, p2.name, ip2_name)
                    ports_connected += 1
        info(
            f"number of ports matched: {ports_connected} for interfaces:"
            f"{ip1_name}:{iface1} - {ip2_name}:{iface2}"
        )

    def _set_port(self, ip: IPWrapper, port_name: str, external_name: str, external_dir: PortDirection) -> None:
        """Set port specified by name as an external port

        :type ip: IPWrapper
        :type port_name: str
        :type external_name: str
        :type external_dir: PortDirection
        :raises ValueError: if such port doesn't exist
        """
        self._set_unconnected_port(ip.top_name, port_name, external_dir)

        inst_args = getattr(self, ip.top_name)

        name = None
        for inst_arg in inst_args.keys():
            if strip_port_prefix(inst_arg) == port_name:
                name = inst_arg
        if name is None:
            raise ValueError(f'port: "{port_name}" does not exist in ip: ' f"{ip.top_name}")

        if external_name not in [port.name for port in self._ports]:
            sig = inst_args[name]
            sig.name = external_name
            setattr(self, external_name, sig)
            self._ports.append(sig)
        elif name[:2] == "i_" or name[:3] == "io_":
            ext_sig = getattr(self, external_name)
            inst_args[name] = ext_sig
        else:
            # Connections between a single external and many internal ports
            # are allowed for external inputs only
            raise ValueError(
                "Multiple connections to external port"
                f"'{external_name}', that is external output"
            )

    def _set_interface(self, ip: IPWrapper, iface_name: str, external_iface_name: str) -> None:
        """Set interface specified by name as an external interface

        :type ip: IPWrapper
        :type iface_name: str
        :type external_iface_name: str
        :raises ValueError: if such interface doesn't exist
        """
        for port in ip.get_ports_of_interface(iface_name):
            self._set_unconnected_port(ip.top_name, port.name, port.direction)

        inst_args = getattr(self, ip.top_name)

        iface_ports = [
            key for key in inst_args.keys() if strip_port_prefix(key).startswith(iface_name)
        ]
        if not iface_ports:
            raise ValueError(f"no ports exist for interface {iface_name}" f"in ip: {ip.top_name}")

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

    def _set_unconnected_port(self, ip_name: str, port_name: str, external_dir: PortDirection) -> None:
        """Create signal for unconnected port to allow using it as
        external. This is essential since ports that haven't been used have
        no signals assigned to them.
        """
        inst_args = getattr(self, ip_name)
        port = self._ips[ip_name].get_port_by_name(port_name)
        full_name = port_direction_to_prefix(external_dir) + port.name

        if full_name not in inst_args.keys():
            inst_args[full_name] = Signal(len(port), name=full_name)

    def set_constant(self, ip_name: str, ip_port: str, target: int) -> None:
        """Set a constant value on a port of an IP

        :param ip_name: name of the IP
        :param ip_port: name of the port of the IP
        :param target: int value to be assigned
        :raises ValueError: if such IP doesn't exist
        """
        if ip_name not in self._ips.keys():
            raise ValueError(
                f"No such IP in this module: {ip_name}." " Use add_ip method to add the IPs first"
            )

        port = self._ips[ip_name].get_port_by_name(ip_port)
        inst_args = getattr(self, ip_name)
        full_name = port_direction_to_prefix(port.direction) + port.name
        inst_args[full_name] = Const(target)

    def make_connections(self, ports: dict, interfaces: dict) -> None:
        """Use names of port and names of ips to make connections"""
        for ip1_name, connections in ports.items():
            for ip1_port, target in connections.items():
                # target is one of:
                #   - a number (int)
                #   - an external port name
                #   - list of (ip2_name, ip2_port)
                if isinstance(target, int):
                    self.set_constant(ip1_name, ip1_port, target)
                elif isinstance(target, str):
                    pass
                else:
                    (ip2_name, ip2_port) = target
                    self.connect_ports(ip1_port, ip1_name, ip2_port, ip2_name)

        for ip1_name, connections in interfaces.items():
            for ip1_iface, target in connections.items():
                # target is one of:
                #   - an external interface name
                #   - list of (ip2_name, ip2_iface)
                if isinstance(target, str):
                    pass
                else:
                    (ip2_name, ip2_iface) = target
                    self.connect_interfaces(ip1_iface, ip1_name, ip2_iface, ip2_name)

    def make_external_ports_interfaces(self, ports: dict, interfaces: dict, external: dict) -> None:
        """Pick ports and interfaces which will be used as external I/O"""
        ext_ports = {"in": [], "out": [], "inout": []}
        if "ports" in external.keys():
            for dir in external["ports"].keys():
                ext_ports[dir] = external["ports"][dir]

        for ip_name, connections in ports.items():
            for ip_port, target in connections.items():
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

                    # check if port direction matches with the user-specified
                    # direction from the 'externals' section - 'ext_dir'
                    port_dir = self._ips[ip_name].get_port_by_name(ip_port).direction  # noqa: E501
                    # It is illegal to connect:
                    #  - output to output
                    #  - input to input
                    # Any other connection is legal.
                    if port_dir != ext_dir and DIR_INOUT not in (port_dir, ext_dir):
                        raise ValueError(
                            f"Direction of external port '{target}'"
                            f"doesn't match '{ip_name}:{ip_port}' direction"
                        )

                    self._set_port(self._ips[ip_name], ip_port, target, ext_dir)

        ext_ifaces = []
        if "interfaces" in external.keys():
            for dir in external["interfaces"].keys():
                ext_ifaces += external["interfaces"][dir]

        for ip_name, connections in interfaces.items():
            for ip_iface, target in connections.items():
                if isinstance(target, str):
                    if target not in ext_ifaces:
                        raise ValueError(
                            f"External interface '{target}'" "not found in 'externals' section"
                        )
                    self._set_interface(self._ips[ip_name], ip_iface, target)

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

        for ip in self._ips.values():
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
        for ip_name in self._ips.keys():
            args = getattr(self, ip_name)
            try:
                inst = Instance(ip_name, **args)
                setattr(m.submodules, ip_name, inst)
            except TypeError:
                error(f"couldn't create instance of {ip_name} " f"using args: {args}")

        return m
