# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC
from typing import Any, Generic, TypeVar

import topwrap_axi_core_plugin
from amaranth.back import verilog

import topwrap.backend.sv.wishbone_interconnect as wb_inter
from topwrap.backend.generator import Generator
from topwrap.backend.sv.common import SVFile, SVFileType
from topwrap.interconnects.axi import AXIInterconnect
from topwrap.interconnects.wishbone_rr import WishboneInterconnect
from topwrap.model.connections import (
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import ModuleInstance
from topwrap.model.hdl_types import Bit
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import (
    Interface,
    InterfaceMode,
    InterfaceSignal,
)
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

_IT = TypeVar("_IT", bound=Interconnect)


PULP_AXI_VERILOGWRITER_NAME = "verilogwriter.py"
PULP_AXI_AXIINTERCONGEN_NAME = "axi_intercon_gen.py"


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


class AXIVerilogGenerator(SystemVerilogGenerator[AXIInterconnect]):
    _signals = [
        ("aw", "id"),
        ("aw", "addr"),
        ("aw", "len"),
        ("aw", "size"),
        ("aw", "burst"),
        ("aw", "lock"),
        ("aw", "cache"),
        ("aw", "prot"),
        ("aw", "region"),
        ("aw", "qos"),
        ("aw", "atop"),
        ("aw", "valid"),
        ("aw", "ready"),
        ("aw", "user"),
        ("ar", "id"),
        ("ar", "addr"),
        ("ar", "len"),
        ("ar", "size"),
        ("ar", "burst"),
        ("ar", "lock"),
        ("ar", "cache"),
        ("ar", "prot"),
        ("ar", "region"),
        ("ar", "qos"),
        ("ar", "valid"),
        ("ar", "ready"),
        ("ar", "user"),
        ("w", "data"),
        ("w", "strb"),
        ("w", "last"),
        ("w", "valid"),
        ("w", "ready"),
        ("w", "user"),
        ("b", "id"),
        ("b", "resp"),
        ("b", "valid"),
        ("b", "ready"),
        ("b", "user"),
        ("r", "id"),
        ("r", "data"),
        ("r", "resp"),
        ("r", "last"),
        ("r", "valid"),
        ("r", "ready"),
        ("r", "user"),
    ]

    def generate(self, interconnect: AXIInterconnect, module_instance: ModuleInstance) -> SVFile:
        config = {
            "parameters": {
                "slaves": {},
                "masters": {},
                "atop": interconnect.params.atop,
            },
            "vlnv": "vendor:library:axi_intercon:1.0",
        }

        subordinate_names = []
        for manager_id in interconnect.subordinates:
            referenced_interface = manager_id.resolve()
            subordinate = interconnect.subordinates[manager_id]
            instance_name = None
            if referenced_interface.instance is not None:
                instance_name = referenced_interface.instance.name
            else:
                instance_name = f"id_{referenced_interface._id._id}"
            name = f"{instance_name}_{referenced_interface.io.name}"
            config["parameters"]["slaves"][name] = {
                "offset": subordinate.address.elaborate(),
                "size": subordinate.size.elaborate(),
            }
            subordinate_names.append(name)

        for manager_id in interconnect.managers:
            manager = interconnect.managers[manager_id]
            referenced_interface = manager_id.resolve()
            instance_name = None
            if referenced_interface.instance is not None:
                instance_name = referenced_interface.instance.name
            else:
                instance_name = f"id_{referenced_interface._id._id}"
            name = f"{instance_name}_{referenced_interface.io.name}"
            config["parameters"]["masters"][name] = {
                "id_width": manager.id_width.elaborate(),
                "slaves": subordinate_names,
            }

        name = f"interconnect_{interconnect.name}"

        out = topwrap_axi_core_plugin.generate_interconnect(config, name)

        return SVFile(content=out, name=name, type=SVFileType.MODULE)

    def get_name(self, referenced_interface: ReferencedInterface, signal: InterfaceSignal) -> str:
        instance_name = None
        if referenced_interface.instance is not None:
            instance_name = referenced_interface.instance.name
        else:
            instance_name = f"id_{referenced_interface._id._id}"
        mode_subordinate = referenced_interface.io.mode == InterfaceMode.SUBORDINATE
        mode = InterfaceMode.MANAGER if mode_subordinate else InterfaceMode.SUBORDINATE
        direction = signal.modes[mode].direction
        direction_str = (
            "o" if direction == PortDirection.OUT else "i" if direction == PortDirection.IN else ""
        )
        name = (
            f"{direction_str}_{instance_name}_{referenced_interface.io.name}_{signal.name.lower()}"
        )
        return name

    def _add_clk_and_rst_ports_to_design(
        self,
        module: Module,
        module_instance: ModuleInstance,
        interconnect: AXIInterconnect,
    ):
        design = interconnect.parent
        for port_name, source in [("clk_i", interconnect.clock), ("rst_ni", interconnect.reset)]:
            port = Port(name=port_name, direction=PortDirection.IN, type=Bit())
            module.add_port(port)
            design.add_connection(
                PortConnection(
                    target=ReferencedPort(io=port, instance=module_instance),
                    source=source,
                )
            )

    def add_module_instance_to_design(
        self,
        interconnect: AXIInterconnect,
    ) -> ModuleInstance:
        """
        Returns `ModuleInstance` with ports interfaces generated based on `Interconnect`
        `ModuleInstance` and connections are added to design

        :param interconnect: `Interconnect` to represent as `ModuleInstance`
        """
        module = Module(
            id=Identifier(f"interconnect_{interconnect.name}"),
            design=None,
        )

        design = interconnect.parent

        module_instance = ModuleInstance(name=interconnect.name, module=module)

        self._add_clk_and_rst_ports_to_design(
            module=module, module_instance=module_instance, interconnect=interconnect
        )

        for managers_or_subordinates, interface_mode in [
            (interconnect.managers, InterfaceMode.SUBORDINATE),
            (interconnect.subordinates, InterfaceMode.MANAGER),
        ]:
            for referenced_interface_id in managers_or_subordinates:
                referenced_interface = referenced_interface_id.resolve()
                interface = referenced_interface.io
                signals = {}
                for signal in interface.definition.signals:
                    for valid_signal in self._signals:
                        if "".join(valid_signal) == signal.name.lower():
                            break
                    else:
                        continue
                    if "atop" in signal.name.lower() and not interconnect.params.atop:
                        continue
                    if (
                        "user" in signal.name.lower()
                        # Upstream PULP script does not support setting user signals width
                    ):
                        continue
                    port = Port(
                        name=self.get_name(referenced_interface, signal),
                        direction=signal.modes[interface_mode].direction,
                        type=signal.type,
                    )
                    module.add_port(port)
                    signals[signal._id] = ReferencedPort(io=port)

                new_interface = Interface(
                    name=f"{interface.name}_{interface.parent.id.name}",
                    mode=interface_mode,
                    definition=interface.definition,
                    signals=signals,
                )
                module.add_interface(new_interface)
                design.add_connection(
                    InterfaceConnection(
                        source=referenced_interface,
                        target=ReferencedInterface(io=new_interface, instance=module_instance),
                    )
                )

        design.add_component(module_instance)
        return module_instance


#: Used by SV backend to get correct generator. All implementations of `Generator`
#: for SV backend need to be present in this map.
verilog_generators_map: dict[type[Interconnect], type[SystemVerilogGenerator[Any]]] = {
    WishboneInterconnect: WishboneRRSystemVerilogGenerator,
    AXIInterconnect: AXIVerilogGenerator,
}
