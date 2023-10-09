# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from typing import List

from .amaranth_helpers import WrapperPort
from .wrapper import Wrapper


class HierarchyWrapper(Wrapper):
    """This class is a wrapper for hierarchies - in fact it is IPConnect to IPWrapper adapter.

    On one hand, the hierarchies are created with IPConnect class since they are a group of IP cores
    (or nested hierarchies) connected together.
    But on the other hand there must be an ability to put an existing hierarchy into a higher-level
    one - this is achieved by wrapping IPConnect with HierarchyWrapper.
    """

    def __init__(self, name: str, ipc) -> None:
        super().__init__(name)
        self.ipc = ipc

    @property
    def _ports(self):
        return self.ipc.get_ports()

    def elaborate(self, platform):
        m = Module()
        m.submodules.ipc = self.ipc
        return m
