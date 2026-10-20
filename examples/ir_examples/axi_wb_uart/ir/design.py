# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.connections import (
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.interface import Interface, InterfaceMode
from topwrap.model.misc import ElaboratableValue, Identifier
from topwrap.model.module import Module

from ...SoC_AXI.ir.axi import interconnect_axi

awaddr = interconnect_axi.signals.find_by_name_or_error("awaddr")
awvalid = interconnect_axi.signals.find_by_name_or_error("awvalid")
awready = interconnect_axi.signals.find_by_name_or_error("awready")
wdata = interconnect_axi.signals.find_by_name_or_error("wdata")
first_awaddr = Port(
    name="first_awaddr",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
)
first_awvalid = Port(name="first_awvalid", direction=PortDirection.IN)
first_awready = Port(name="first_awready", direction=PortDirection.OUT)
first_wdata = Port(
    name="first_wdata",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(63))]),
)
second_awaddr = Port(
    name="second_awaddr",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
)
second_awvalid = Port(name="second_awvalid", direction=PortDirection.IN)
second_awready = Port(name="second_awready", direction=PortDirection.OUT)
second_wdata = Port(
    name="second_wdata",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(63))]),
)
clk = Port(name="clk", direction=PortDirection.IN)
first_r_port_had_funny_name = Port(name="first_r_port_had_funny_name", direction=PortDirection.IN)
first = Interface(
    name="first",
    mode=InterfaceMode.SUBORDINATE,
    definition=interconnect_axi,
    signals={
        wdata._id: ReferencedPort.external(first_wdata),
        awready._id: ReferencedPort.external(first_awready),
        awvalid._id: ReferencedPort.external(first_awvalid),
        awaddr._id: ReferencedPort.external(first_awaddr),
    },
)
second = Interface(
    name="second",
    mode=InterfaceMode.SUBORDINATE,
    definition=interconnect_axi,
    signals={
        wdata._id: ReferencedPort.external(second_wdata),
        awready._id: ReferencedPort.external(second_awready),
        awvalid._id: ReferencedPort.external(second_awvalid),
        awaddr._id: ReferencedPort.external(second_awaddr),
    },
)
module = Module(
    id=Identifier(name="port_order_device"),
    ports=[
        first_r_port_had_funny_name,
        clk,
        second_wdata,
        first_wdata,
        second_awready,
        first_awready,
        second_awvalid,
        first_awvalid,
        second_awaddr,
        first_awaddr,
    ],
    interfaces=[first, second],
)
device = ModuleInstance(name="device", module=module)
top_first_awaddr = Port(
    name="first_awaddr",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
)
top_first_awvalid = Port(name="first_awvalid", direction=PortDirection.IN)
top_first_awready = Port(name="first_awready", direction=PortDirection.OUT)
top_first_wdata = Port(
    name="first_wdata",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(63))]),
)
top_second_awaddr = Port(
    name="second_awaddr",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(31))]),
)
top_second_awvalid = Port(name="second_awvalid", direction=PortDirection.IN)
top_second_awready = Port(name="second_awready", direction=PortDirection.OUT)
top_second_wdata = Port(
    name="second_wdata",
    direction=PortDirection.IN,
    type=Bits(dimensions=[Dimensions(ElaboratableValue(63))]),
)
top_clk = Port(name="clk", direction=PortDirection.IN)
top_first_r_port_had_funny_name = Port(
    name="first_r_port_had_funny_name", direction=PortDirection.IN
)
top_first = Interface(
    name="first",
    mode=InterfaceMode.SUBORDINATE,
    definition=interconnect_axi,
    signals={
        wdata._id: ReferencedPort.external(top_first_wdata),
        awready._id: ReferencedPort.external(top_first_awready),
        awvalid._id: ReferencedPort.external(top_first_awvalid),
        awaddr._id: ReferencedPort.external(top_first_awaddr),
    },
)
top_second = Interface(
    name="second",
    mode=InterfaceMode.SUBORDINATE,
    definition=interconnect_axi,
    signals={
        wdata._id: ReferencedPort.external(top_second_wdata),
        awready._id: ReferencedPort.external(top_second_awready),
        awvalid._id: ReferencedPort.external(top_second_awvalid),
        awaddr._id: ReferencedPort.external(top_second_awaddr),
    },
)
top = Module(
    id=Identifier(name="port_order_top"),
    ports=[
        top_first_r_port_had_funny_name,
        top_clk,
        top_second_wdata,
        top_first_wdata,
        top_second_awready,
        top_first_awready,
        top_second_awvalid,
        top_first_awvalid,
        top_second_awaddr,
        top_first_awaddr,
    ],
    interfaces=[top_first, top_second],
    design=Design(
        components=[device],
        connections=[
            InterfaceConnection(
                source=ReferencedInterface.external(top_first),
                target=ReferencedInterface(instance=device, io=first),
            ),
            InterfaceConnection(
                source=ReferencedInterface.external(top_second),
                target=ReferencedInterface(instance=device, io=second),
            ),
            PortConnection(
                source=ReferencedPort.external(top_clk),
                target=ReferencedPort(instance=device, io=clk),
            ),
            PortConnection(
                source=ReferencedPort.external(top_first_r_port_had_funny_name),
                target=ReferencedPort(instance=device, io=first_r_port_had_funny_name),
            ),
        ],
    ),
)
