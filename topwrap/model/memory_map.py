# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, Optional

from topwrap.model.connections import ReferencedInterface
from topwrap.model.misc import ElaboratableValue, ModelBase

if TYPE_CHECKING:
    from topwrap.model.design import Design


class MemoryMapSubordinate(ModelBase):
    parameters: dict[str, ElaboratableValue]
    ref_iface: ReferencedInterface

    def __init__(self, ref_iface: ReferencedInterface, parameters: dict[str, ElaboratableValue]):
        super().__init__()
        self.ref_iface = ref_iface
        self.parameters = parameters


class MemoryMap(ModelBase):
    name: str
    map: dict[int, MemoryMapSubordinate]
    parent: Optional["Design"]

    def __init__(self, name: str, map: dict[int, MemoryMapSubordinate]):
        super().__init__()
        self.name = name
        self.map = map
        self.parent = None
