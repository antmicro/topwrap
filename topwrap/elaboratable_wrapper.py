# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

# Disabled due to Amaranth imports
# ruff: noqa: F405

from functools import lru_cache
from typing import Iterable, List, Mapping, Union

from amaranth import *  # noqa: F403
from amaranth.build import Platform
from amaranth.hdl.ast import Assign, Shape
from amaranth.lib import wiring

from .amaranth_helpers import DIR_IN, DIR_OUT, WrapperPort
from .wrapper import Wrapper

SignalMapping = Mapping[str, Union[Signal, "SignalMapping"]]
InterfaceLike = Union[wiring.PureInterface, Elaboratable]


class ElaboratableWrapper(Wrapper):
    """Allows connecting an Amaranth's Elaboratable with other
    classes derived from Wrapper.
    """

    def __init__(self, name: str, elaboratable: Elaboratable) -> None:
        """
        :param name: name of this wrapper
        :param elaboratable: Amaranth's Elaboratable object to wrap
        """
        super().__init__(name)
        self.elaboratable = elaboratable
        self.clk = ElaboratableWrapper._cached_wrapper(
            port_width=1, port_flow=wiring.In, name="clk", port_name="clk", iface_name=""
        )
        self.rst = ElaboratableWrapper._cached_wrapper(
            port_width=1, port_flow=wiring.In, name="rst", port_name="rst", iface_name=""
        )

    def get_ports(self) -> List[WrapperPort]:
        """Return a list of external ports."""
        return self._flatten_hier(self.get_ports_hier())

    def get_ports_hier(self) -> SignalMapping:
        """Maps elaboratable's Signature to a nested dictionary of WrapperPorts.
        See _gather_signature_ports for more details.
        """
        ports = self._gather_signature_ports(self.elaboratable.signature)
        ports.update(
            {
                "clk": self.clk,
                "rst": self.rst,
            }
        )
        return ports

    @staticmethod
    @lru_cache(maxsize=None)
    def _cached_wrapper(
        port_width: int, port_flow: wiring.Flow, name: str, port_name: str, iface_name: str
    ) -> WrapperPort:
        """Constructs a WrapperPort, but only one instance per set of parameters in
        a module is ever created. Multiple calls to this function with the identical
        parameters return the same object.

        :param port_width: width of the port
        :param port_flow: directionality of the port, one of: wiring.In, wiring.Out
        :param name: name of the port
        :param port_name: original port name as it appears in the signature
        :param iface_name: name of the interface the ports belongs to
        """
        return WrapperPort(
            bounds=[port_width - 1, 0, port_width - 1, 0],
            name=name,
            internal_name=port_name,
            interface_name=iface_name,
            direction=DIR_IN if port_flow == wiring.In else DIR_OUT,
        )

    def _gather_signature_ports(
        self, signature: wiring.Signature, prefix: str = ""
    ) -> SignalMapping:
        """Maps a signature to a nested dictionary of WrapperPorts.
        For example, an elaboratable with this signature:

            Signature({
                "data": Out(Signature({
                    "payload": Out(7),
                    "chksum": Out(1)
                })),
                "ready": In(1),
                "valid": Out(1)
            })

        Translates to this dictionary structure (some details omitted for clarity):

            {
                "data": {
                    "payload": WrapperPort(
                        bounds=[6, 0, 6, 0],
                        name="data_payload",
                        internal_name="payload",
                        interface_name="data",
                        direction=DIR_OUT
                    ),
                    "chksum": WrapperPort(...)
                },
                "ready": WrapperPort(
                    bounds=[0, 0, 0, 0],
                    name="ready",
                    internal_name="ready",
                    interface_name="",
                    direction=DIR_IN
                ),
                "valid": WrapperPort(...)
            }

        :param signature: Amaranth's Signature to map to a dictionary
        :param prefix: optional interface prefix to prepend to the name of all ports
        """
        iface = {}
        for port_name, port in signature.members.items():
            name = f"{prefix}_{port_name}" if prefix else port_name
            if port.is_signature:
                inner_iface = self._gather_signature_ports(port.signature, prefix=name)
                iface[port_name] = inner_iface
            else:
                iface[port_name] = ElaboratableWrapper._cached_wrapper(
                    Shape.cast(port.shape).width, port.flow, name, port_name, prefix
                )
        return iface

    def _flatten_hier(self, hier: SignalMapping) -> Iterable[Signal]:
        """Flattens a nested dictionary with WrapperPorts.

        :param hier: a (nested) dictionary of WrapperPorts
        """
        ports = []
        try:
            for _, port in hier.items():
                ports += self._flatten_hier(port)
        except AttributeError:
            ports += [hier]
        return ports

    def _connect_ports(self, ports: SignalMapping, iface: InterfaceLike) -> List[Assign]:
        """Returns a list of amaranth assignments between the wrapped elaboratable and external
        ports.

        :param ports: nested dictionary of WrapperPorts mirroring that of iface's signature
        :param iface: Amaranth Interface to make connections with
        """
        conns = []
        for port_name, port in iface.signature.members.items():
            iface_port = getattr(iface, port_name)
            if port.is_signature:
                conns += self._connect_ports(ports[port_name], iface_port)
            else:
                if port.flow == wiring.In:
                    conns.append(iface_port.eq(ports[port_name]))
                elif port.flow == wiring.Out:
                    conns.append(ports[port_name].eq(iface_port))
                else:
                    raise TypeError(f"Invalid InOut flow direction in signal '{port_name}'")
        return conns

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        # create an internal clock domain that doesn't propagate upwards in the submodule
        # tree and assign clk and rst specified by the user to the internal domain signals
        cd = ClockDomain(self.name, local=True)
        m.d.comb += ClockSignal(self.name).eq(self.clk)
        m.d.comb += ResetSignal(self.name).eq(self.rst)
        m.domains += cd

        # make the elaboratable use the new clock domain internally
        m.submodules += DomainRenamer(self.name)(self.elaboratable)

        m.d.comb += self._connect_ports(self.get_ports_hier(), self.elaboratable)

        return m
