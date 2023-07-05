# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from os import path, makedirs
from logging import warning, info, error
from amaranth import Elaboratable, Module, Signal, Instance, Fragment
from amaranth.hdl.ast import Const
from amaranth.build import Platform
from amaranth.back import verilog
from .ipwrapper import IPWrapper
from .nm_helper import port_direction_to_prefix
from .fuse_helper import FuseSocBuilder


class IPConnect(Elaboratable):
    """Connector for multiple IPs, capable of connecting their interfaces
    as well as individual ports.
    """

    def __init__(self):
        self._signals_between_ips = []
        self._ips = dict()
        self._ips_by_internal_name = dict()
        self._ports = []

    def add_ip(self, ip: IPWrapper):
        """Add a new IPWrapper object, allowing to make connections with it"""
        ip_name = ip.top_name
        self._ips[ip_name] = ip
        self._ips_by_internal_name[ip.ip_name] = ip
        # create a placeholder for Instance arguments to instantiate the ip
        setattr(self, ip_name, dict())

    def connect_ports(self, port1_name: str, ip1_name: str,
                      port2_name: str, ip2_name: str):
        """Connect ports of IPs previously added to this Connector

        :param port1_name: name of the port of the 1st IP
        :param ip1_name: name of the 1st IP
        :param port2_name: name of the port of the 2nd IP
        :param ip2_name: name of the 2nd IP
        :raises ValueError: if such IP doesn't exist
        """
        if (ip1_name not in self._ips.keys() or
                ip2_name not in self._ips.keys()):
            raise ValueError(
                f'No such IP in this module: {ip1_name}, {ip2_name}.'
                ' Use add_ip method to add the IPs first')
        # get the 'WrapperPort's
        port1 = self._ips[ip1_name].get_port_by_name(port1_name)
        port2 = self._ips[ip2_name].get_port_by_name(port2_name)

        if len(port1) != len(port2):
            warning(f'ports: {ip1_name}:{port1.name}({len(port1)}), '
                    f'{ip2_name}:{port2.name}({len(port2)})'
                    ' have different widths!')

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
            combined_name = port1.name + '_' + port2.name
            self._signals_between_ips.append(combined_name)
            sig = Signal(len(port1), name=combined_name)
            setattr(self, combined_name, sig)

        inst1_args[full_name1] = sig
        inst2_args[full_name2] = sig

    def connect_interfaces(self, iface1: str, ip1_name: str,
                           iface2: str, ip2_name: str):
        """Make connections between all matching ports of the interfaces

        :param iface1: name of the 1st interface
        :param ip1_name: name of the 1st IP
        :param iface2: name of the 2nd interface
        :param ip2_name: name of the 2nd IP
        :raises ValueError: if any of the IPs doesn't exist
        """
        if (ip1_name not in self._ips.keys() or
                ip2_name not in self._ips.keys()):
            raise ValueError(
                f'No such IP in this module: {ip1_name}, {ip2_name}.'
                ' Use add_ip method to add the IPs first')

        ip1_ports = self._ips[ip1_name].get_ports_of_interface(iface1)
        ip2_ports = self._ips[ip2_name].get_ports_of_interface(iface2)

        ip1_signames = {p.name.split('_')[-1] for p in ip1_ports}
        ip2_signames = {p.name.split('_')[-1] for p in ip2_ports}
        ip1_unconnected = ip1_signames - ip2_signames
        ip2_unconnected = ip2_signames - ip1_signames
        if ip1_unconnected:
            info('Unconnected signals of '
                 f'{ip1_name}:{iface1}: {ip1_unconnected}')
        if ip2_unconnected:
            info('Unconnected signals of '
                 f'{ip2_name}:{iface2} {ip2_unconnected}')

        ports_connected = 0
        for p1 in ip1_ports:
            for p2 in ip2_ports:
                names_match = p1.name.split('_')[-1] == p2.name.split('_')[-1]
                # widths_match = len(p1) == len(p2)
                if names_match:
                    self.connect_ports(p1.name, ip1_name, p2.name, ip2_name)
                    ports_connected += 1
        info(f'number of ports matched: {ports_connected} for interfaces:'
             f'{ip1_name}:{iface1} - {ip2_name}:{iface2}')

    def _set_port(self, ip, port_name):
        """Set port specified by name as an external port

        :type ip: IPWrapper
        :type port_name: str
        :raises ValueError: if such port doesn't exist
        """

        inst_args = getattr(self, ip.top_name)
        try:
            name = [key for key in inst_args.keys() if key[2:] == port_name][0]
        except IndexError:
            raise ValueError(f'port: "{port_name}" does not exist in ip: '
                             f'{ip.top_name}')
        sig = inst_args[name]
        sig.name = port_name
        setattr(self, port_name, sig)
        self._ports.append(sig)

    def _set_interface(self, ip, iface_name):
        """Set interface specified by name as an external interface

        :type ip: IPWrapper
        :type iface_name: str
        :raises ValueError: if such interface doesn't exist
        """
        inst_args = getattr(self, ip.top_name)

        iface_ports = [
            key for key in inst_args.keys() if key[2:].startswith(iface_name)
        ]
        if not iface_ports:
            raise ValueError(
                f'no ports exist for interface {iface_name}'
                f'in ip: {ip.top_name}'
            )

        for iface_port in iface_ports:
            sig = inst_args[iface_port]
            setattr(self, iface_port, sig)
            self._ports.append(sig)

    def get_ports(self):
        """Return a list of external ports of this module
        """
        return self._ports

    def _set_unconnected_ports(self):
        """Create signals for unconnected ports to allow using them as
        external. This is essential since ports that haven't been used have
        no signals assigned to them.
        """
        for name, ip in self._ips.items():
            count = 0
            inst_args = getattr(self, name)
            ports = ip.get_ports()
            for port in ports:
                full_name = (port_direction_to_prefix(port.direction)
                             + port.name)
                if full_name not in inst_args.keys():
                    sig = Signal(len(port), name=full_name)
                    inst_args[full_name] = sig
                    count += 1

    def set_constant(self, ip_name, ip_port, target):
        """Set a constant value on a port of an IP

        :param ip_name: name of the IP
        :param ip_port: name of the port of the IP
        :param target: int value to be assigned
        :raises ValueError: if such IP doesn't exist
        """
        if ip_name not in self._ips.keys():
            raise ValueError(
                f'No such IP in this module: {ip_name}.'
                ' Use add_ip method to add the IPs first')

        port = self._ips[ip_name].get_port_by_name(ip_port)
        inst_args = getattr(self, ip_name)
        full_name = port_direction_to_prefix(port.direction) + port.name
        inst_args[full_name] = Const(target)

    def make_connections(self, ports, interfaces):
        """Use names of port and names of ips to make connections
        """
        for ip1_name, connections in ports.items():
            for ip1_port, target in connections.items():
                # target is one of:
                #   - a number (int)
                #   - list of (ip2_name, ip2_port)
                if isinstance(target, int):
                    self.set_constant(ip1_name, ip1_port, target)
                else:
                    (ip2_name, ip2_port) = target
                    self.connect_ports(ip1_port, ip1_name,
                                       ip2_port, ip2_name)

        for ip1_name, connections in interfaces.items():
            for ip1_iface, (ip2_name, ip2_iface) in connections.items():
                self.connect_interfaces(ip1_iface, ip1_name,
                                        ip2_iface, ip2_name)

    def make_external_ports_interfaces(self, ports_ifaces):
        """Pick ports and interfaces which will be used as external I/O

        :param ports_ifaces: dict {'in': {ip_name: port_name}, 'out': ...}
        """
        _exts = {}
        for dir in ports_ifaces.keys():
            for ip_name, externals_list in ports_ifaces[dir].items():
                if ip_name not in _exts.keys():
                    _exts[ip_name] = externals_list
                else:
                    _exts[ip_name] += externals_list

        self._set_unconnected_ports()
        for ip_name, _ip_exts in _exts.items():
            ifaces_names = [
                p.interface_name for p in self._ips[ip_name].get_ports()]
            for _ext in _ip_exts:
                if _ext in ifaces_names:
                    self._set_interface(self._ips[ip_name], _ext)
                else:
                    self._set_port(self._ips[ip_name], _ext)

    def build(self, build_dir='build', template=None, sources_dir=None,
              top_module_name='project_top', part=None):
        # This class is used for generating FuseSoC Core file
        fuse = FuseSocBuilder(part)

        for ip in self._ips.values():
            filename = ip.top_name + '.v'
            fuse.add_source(filename, 'verilogSource')

            makedirs(build_dir,exist_ok=True)
            target_file = open(path.join(build_dir, filename), 'w')

            fragment = Fragment.get(ip, None)

            output = verilog.convert(fragment, name=ip.top_name,
                                     ports=ip.get_ports())
            target_file.write(output)

        fuse.add_source(top_module_name + '.v', 'verilogSource')
        fuse.build(path.join(build_dir, 'top.core'), sources_dir=sources_dir)
        target_file = open(path.join(build_dir, top_module_name + '.v'), 'w')

        fragment = Fragment.get(self, None)
        output = verilog.convert(fragment, name=top_module_name,
                                 ports=self.get_ports())
        target_file.write(output)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        for ip_name in self._ips.keys():
            args = getattr(self, ip_name)
            try:
                inst = Instance(ip_name, **args)
                setattr(m.submodules, ip_name, inst)
            except TypeError:
                error(f"couldn't create instance of {ip_name} "
                      f"using args: {args}")

        return m
