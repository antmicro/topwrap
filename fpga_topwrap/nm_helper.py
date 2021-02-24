# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from nmigen import Signal
from nmigen.hdl.rec import Direction, DIR_FANIN, DIR_FANOUT


def port_direction_to_prefix(direction: Direction) -> str:
    """Return a port prefix that is required by Instance class in nMigen,

    :rtype: str
    """
    if direction == DIR_FANIN:
        return 'i_'
    elif direction == DIR_FANOUT:
        return 'o_'
    else:
        return 'io_'


class WrapperPort(Signal):
    def __init__(self, bounds, name, internal_name, direction, interface_name):
        '''
        Wraps a port, adding a new name and optionally slicing the signal

        :param bounds[0:1]: upper and lower bounds of reference signal
        :param bounds[2:3]: upper and lower bounds of internal port,
            which are either the same as reference port,
            or a slice of the reference port

        :param name: a new name for the signal
        :param internal_name: name of the port to be wrapped/sliced
        :param direction: one of nmigen.hdl.rec.Direction, e.g. DIR_FANOUT
        '''

        super().__init__(shape=bounds[2]-bounds[3]+1, name=name)
        # port name of the wrapped IP
        self.internal_name = internal_name
        self.direction = direction
        self.interface_name = interface_name
        self.bounds = bounds
