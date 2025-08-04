# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC
from typing import Any, Generic, TypeVar

from amaranth.back import verilog

import topwrap.backend.sv.wishbone_interconnect as wb_inter
from topwrap.backend.generator import Generator
from topwrap.backend.sv.common import SVFile, SVFileType
from topwrap.interconnects.wishbone_rr import WishboneInterconnect
from topwrap.model.connections import (
    ReferencedInterface,
)
from topwrap.model.design import ModuleInstance
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import (
    InterfaceSignal,
)
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

_IT = TypeVar("_IT", bound=Interconnect)


class SystemVerilogGenerator(Generator[SVFile, _IT], ABC, Generic[_IT]):
    """
    It is System Verilog specific generator, it's empty and need subclass for each Interconnect
    that SV backend need to support
    """

    ...


class WishboneRRSystemVerilogGenerator(SystemVerilogGenerator[WishboneInterconnect]):
    @staticmethod
    def generate_instance_name(referenced_interface: ReferencedInterface) -> str:
        instance_name = None
        if referenced_interface.instance is not None:
            instance_name = referenced_interface.instance.name
        else:
            instance_name = f"id_{referenced_interface._id._id}"
        return f"{instance_name}_{referenced_interface.io.name}"

    def generate(
        self, interconnect: WishboneInterconnect, module_instance: ModuleInstance
    ) -> SVFile:
        wb_params = interconnect.params
        features = frozenset([x.value for x in interconnect.params.features])
        ic = wb_inter.WishboneRRInterconnect(
            addr_width=int(wb_params.addr_width.value),
            data_width=int(wb_params.data_width.value),
            granularity=wb_params.granularity,
            features=features,
        )

        for referenced_interface_id in interconnect.managers:
            referenced_interface = referenced_interface_id.resolve()
            ic.add_manager(name=self.generate_instance_name(referenced_interface))

        for referenced_interface_id in interconnect.subordinates:
            referenced_interface = referenced_interface_id.resolve()
            subordinate = interconnect.subordinates[referenced_interface_id]
            ic.add_subordinator(
                name=self.generate_instance_name(referenced_interface),
                addr=int(subordinate.address.value),
                size=int(subordinate.size.value),
            )

        return SVFile(
            content=verilog.convert(ic, name=f"interconnect_{interconnect.name}"),
            name=f"interconnect_{interconnect.name}",
            type=SVFileType.MODULE,
        )

    def get_name(self, referenced_interface: ReferencedInterface, signal: InterfaceSignal) -> str:
        return f"{self.generate_instance_name(referenced_interface)}__{signal.name}"

    def add_module_instance_to_design(
        self,
        interconnect: WishboneInterconnect,
    ) -> ModuleInstance:
        """
        Returns generated `ModuleInstance` based on `Interconnect`, generated `ModuleInstance`
        always has `rst` and `clk`, `ModuleInstance` also has additional ports and interfaces based
        on what bus is used with managers and subordinates. `ModuleInstance`s of subordinates and
        managers are connected to generated `ModuleInstance`

        :param interconnect: `Interconnect` to represent as `ModuleInstance`
        """
        module = Module(
            id=Identifier(f"interconnect_{interconnect.name}"),
            design=None,
        )
        design = interconnect.parent

        module_instance = ModuleInstance(name=interconnect.name, module=module)

        # generated interconnect by amaranth don't use sequential logic when there is one master
        if len(interconnect.managers) > 1:
            self._add_clk_and_rst_ports_to_design(
                module=module, module_instance=module_instance, interconnect=interconnect
            )

        self._add_interfaces_from_subordinates_and_managers(
            interconnect=interconnect, module_instance=module_instance
        )
        design.add_component(module_instance)
        return module_instance


#: Used by SV backend to get correct generator. All implementations of `Generator`
#: for SV backend need to be present in this map.
verilog_generators_map: dict[type[Interconnect], type[SystemVerilogGenerator[Any]]] = {
    WishboneInterconnect: WishboneRRSystemVerilogGenerator,
}
