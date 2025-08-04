# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import copy
from typing import Any

import pytest

from examples.soc.ir.design import design as soc_design
from topwrap.backend.generator import CLK_PORT_NAME, RST_PORT_NAME, Generator
from topwrap.backend.sv.design import Design
from topwrap.backend.sv.generators import verilog_generators_map
from topwrap.model.connections import (
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.hdl_types import (
    Bit,
)
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import InterfaceMode


class TestInterconnectGeneration:
    @pytest.mark.parametrize(
        ["design", "generators_map"],
        [
            (copy.deepcopy(soc_design), verilog_generators_map),
        ],
    )
    def test_interconnect_port_IR_generation(
        self,
        design: Design,
        generators_map: dict[type[Interconnect], type[Generator[Any, Interconnect]]],
    ):
        for interconnect in design.interconnects:
            generator = generators_map[type(interconnect)]()
            module_instance = generator.add_module_instance_to_design(interconnect)

            for name in [
                CLK_PORT_NAME,
                RST_PORT_NAME,
            ]:
                port = module_instance.module.ports.find_by_name(name)
                assert port is not None
                assert port.direction == PortDirection.IN
                assert port.type == Bit()

            for man_or_subor, mode in [
                (interconnect.managers, InterfaceMode.SUBORDINATE),
                (interconnect.subordinates, InterfaceMode.MANAGER),
            ]:
                for man_or_subor_id in man_or_subor:
                    referenced_interface = man_or_subor_id.resolve()
                    interface = referenced_interface.io
                    for signal in interface.definition.signals:
                        port = module_instance.module.ports.find_by_name(
                            generator.get_name(referenced_interface, signal)
                        )
                        assert port is not None
                        assert port.direction == signal.modes[mode].direction
                        assert port.type == signal.type

    @pytest.mark.parametrize(
        ["design", "generators_map"], [(copy.deepcopy(soc_design), verilog_generators_map)]
    )
    def test_interconnect_connection_IR_generation(
        self,
        design: Design,
        generators_map: dict[type[Interconnect], type[Generator[Any, Interconnect]]],
    ):
        for interconnect in design.interconnects:
            generator = generators_map[type(interconnect)]()
            module_instance = generator.add_module_instance_to_design(interconnect)

            for port, name in [
                (interconnect.clock, CLK_PORT_NAME),
                (interconnect.reset, RST_PORT_NAME),
            ]:
                found = False
                connections = design.connections_with(port)
                for connected_IO in connections:
                    if (
                        isinstance(connected_IO, ReferencedPort)
                        and connected_IO.io.parent == module_instance.module
                    ):
                        assert connected_IO.io.name == name
                        assert connected_IO.io.direction == PortDirection.IN
                        found = True
                assert found

            for man_or_subor, mode in [
                (interconnect.managers, InterfaceMode.SUBORDINATE),
                (interconnect.subordinates, InterfaceMode.MANAGER),
            ]:
                for man_or_subor_id in man_or_subor:
                    referenced_interface = man_or_subor_id.resolve()
                    interface = referenced_interface.io
                    [connected_IO] = design.connections_with(io=referenced_interface)
                    assert isinstance(connected_IO, ReferencedInterface)
                    connected_interface = connected_IO.io
                    assert connected_interface.mode == mode
                    assert (
                        connected_interface.name == f"{interface.name}_{interface.parent.id.name}"
                    )
                    assert connected_interface.definition == referenced_interface.io.definition
