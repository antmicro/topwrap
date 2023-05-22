# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from amaranth import Signal
from amaranth.hdl.rec import Direction, DIR_FANIN, DIR_FANOUT


def port_direction_to_prefix(direction: Direction) -> str:
    """Return a port prefix that is required by Instance class in amaranth,

    :rtype: str
    """
    if direction == DIR_FANIN:
        return 'i_'
    elif direction == DIR_FANOUT:
        return 'o_'
    else:
        return 'io_'


class WrapperPort(Signal):
    def __init__(self, shape=None, src_loc_at=0, **kwargs):
        '''
        Wraps a port, adding a new name and optionally slicing the signal

        :param bounds[0:1]: upper and lower bounds of reference signal
        :param bounds[2:3]: upper and lower bounds of internal port,
            which are either the same as reference port,
            or a slice of the reference port

        :param name: a new name for the signal
        :param internal_name: name of the port to be wrapped/sliced
        :param direction: one of amaranth.hdl.rec.Direction, e.g. DIR_FANOUT
        '''

        super().__init__(
            shape=kwargs["bounds"][2]-kwargs["bounds"][3]+1,
            name=kwargs["name"]
        )
        # port name of the wrapped IP
        self.internal_name = kwargs["internal_name"]
        self.direction = kwargs["direction"]
        self.interface_name = kwargs["interface_name"]
        self.bounds = kwargs["bounds"]
