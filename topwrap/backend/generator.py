# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from topwrap.backend.backend import Backend
from topwrap.model.connections import (
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Bit
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import (
    Interface,
    InterfaceMode,
    InterfaceSignal,
)
from topwrap.model.misc import Identifier, ObjectId
from topwrap.model.module import Module

_T = TypeVar("_T")
_IT = TypeVar("_IT", bound=Interconnect)

CLK_PORT_NAME = "clk"
RST_PORT_NAME = "rst"


class GeneratorNotImplementedError(Exception):
    def __init__(self, interconnect: Interconnect, backend: Backend[Any]):
        self.interconnect = interconnect
        self.backend = backend
        self.message = (
            f"Generator for {type(self.interconnect)} not present for backend {type(self.backend)}"
        )
        super().__init__(self.message)


class InterconnectGenerationError(Exception):
    """
    Used when there is problem with generating HDL code.
    """


class Generator(ABC, Generic[_T, _IT]):
    @abstractmethod
    def generate(self, interconnect: _IT, module_instance: ModuleInstance) -> _T:
        """
        Returns generated HDL code wrapped in class specific for backend

        :param interconnect: HDL code is generated based on this `Interconnect`
        :param module_instance: generated based on `Interconnect`,
                                it don't need to be used for generation, but can be helpful
        :raises InterconnectGenerationError: Raised when there is problem with generating HDL code
        """
        pass

    def get_name(self, referenced_interface: ReferencedInterface, signal: InterfaceSignal) -> str:
        """
        Returns name for `InterfaceSignal`,
        generated backend specific code need to have same naming convention

        :param referenced_interface: `InterfaceInstance` containing this `InterfaceSignal`
        :param signal: `Signal` to give name
        """
        instance_name = None
        if referenced_interface.instance is not None:
            instance_name = referenced_interface.instance.name
        else:
            instance_name = referenced_interface.io.parent.id.name
        return f"{instance_name}_{referenced_interface.io.name}__{signal.name}"

    def _add_clk_and_rst_ports_to_design(
        self,
        module: Module,
        module_instance: ModuleInstance,
        interconnect: _IT,
    ):
        design = interconnect.parent
        clk_port = Port(name=CLK_PORT_NAME, direction=PortDirection.IN, type=Bit())
        module.add_port(clk_port)
        design.add_connection(
            PortConnection(
                target=ReferencedPort(io=clk_port, instance=module_instance),
                source=interconnect.clock,
            )
        )

        rst_port = Port(name=RST_PORT_NAME, direction=PortDirection.IN, type=Bit())
        module.add_port(rst_port)
        design.add_connection(
            PortConnection(
                target=ReferencedPort(io=rst_port, instance=module_instance),
                source=interconnect.reset,
            )
        )

    def _add_interface_to_design(
        self,
        referenced_interface_id: ObjectId[ReferencedInterface],
        interface_mode: InterfaceMode,
        module_instance: ModuleInstance,
        design: Design,
    ):
        module = module_instance.module
        referenced_interface = referenced_interface_id.resolve()
        interface = referenced_interface.io
        signals = {}
        for signal in interface.definition.signals:
            # There can be signals that can be only for
            # subordinate, manager or for neither one
            # for more information look at `InterfaceSignal.modes`
            if interface_mode not in signal.modes:
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

    def _add_interfaces_from_subordinates_and_managers(
        self, interconnect: _IT, module_instance: ModuleInstance
    ):
        design = interconnect.parent
        for managers_or_subordinates, interface_mode in [
            (interconnect.managers, InterfaceMode.SUBORDINATE),
            (interconnect.subordinates, InterfaceMode.MANAGER),
        ]:
            for referenced_interface_id in managers_or_subordinates:
                self._add_interface_to_design(
                    referenced_interface_id=referenced_interface_id,
                    design=design,
                    interface_mode=interface_mode,
                    module_instance=module_instance,
                )

    def add_module_instance_to_design(
        self,
        interconnect: _IT,
    ) -> ModuleInstance:
        """
        Returns generated `ModuleInstance` based on `Interconnect`, generated `ModuleInsance`
        always has `rst` and `clk`, `ModuleInstance` also has additional ports and interfaces based
        on what bus is used with managers and subordinates. `ModuleInstance`s of subordinates and
        managers are connected to generated `ModuleInsatnce`

        :param interconnect: `Interconnect` to represent as `ModuleInstance`
        """
        module = Module(
            id=Identifier(f"interconnect_{interconnect.name}"),
            design=None,
        )

        module_instance = ModuleInstance(name=interconnect.name, module=module)

        self._add_clk_and_rst_ports_to_design(
            module=module, module_instance=module_instance, interconnect=interconnect
        )

        self._add_interfaces_from_subordinates_and_managers(
            interconnect=interconnect, module_instance=module_instance
        )

        design = interconnect.parent
        design.add_component(module_instance)
        return module_instance
