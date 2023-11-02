# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from enum import Enum

from amaranth import Signal

PortDirection = Enum("PortDirection", ("INOUT", "OUT", "IN"))

DIR_INOUT = PortDirection.INOUT
DIR_OUT = PortDirection.OUT
DIR_IN = PortDirection.IN


def port_direction_to_prefix(direction: PortDirection) -> str:
    """Return a port prefix that is required by Instance class in amaranth,

    :rtype: str
    """
    if direction == DIR_IN:
        return "i_"
    elif direction == DIR_OUT:
        return "o_"
    else:
        return "io_"


def strip_port_prefix(port_name: str) -> str:
    """Return a port name without the o_/i_/io_ prefix"""
    if port_name[:2] in ["i_", "o_"]:
        return port_name[2:]
    if port_name[:3] == "io_":
        return port_name[3:]
    return port_name


class WrapperPort(Signal):
    def __init__(self, shape=None, src_loc_at=0, **kwargs):
        """
        Wraps a port, adding a new name and optionally slicing the signal

        :param bounds[0:1]: upper and lower bounds of reference signal
        :param bounds[2:3]: upper and lower bounds of internal port,
            which are either the same as reference port,
            or a slice of the reference port

        :param name: a new name for the signal
        :param internal_name: name of the port to be wrapped/sliced
        :param direction: one of PortDirection, e.g. DIR_OUT
        """

        super().__init__(shape=kwargs["bounds"][2] - kwargs["bounds"][3] + 1, name=kwargs["name"])
        # port name of the wrapped IP
        self.internal_name = kwargs["internal_name"]
        self.direction = kwargs["direction"]
        self.interface_name = kwargs["interface_name"]
        self.bounds = kwargs["bounds"]

    @staticmethod
    def like(other, **kwargs):
        base_args = {
            "bounds": other.bounds,
            "name": other.name,
            "internal_name": other.internal_name,
            "direction": other.direction,
            "interface_name": other.interface_name,
        }
        base_args.update(kwargs)
        return WrapperPort(**base_args)
