from topwrap.model.connections import (
    InterfaceConnection,
    Port,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
    ResetPolarity,
)
from topwrap.model.design import ClockDomain, Design, ModuleInstance, ResetDomain
from topwrap.model.misc import Identifier
from topwrap.model.module import Module

from .cdc import axis_cdc
from .receiver import axis_clk_receiver
from .streamer import axis_clk_streamer

external_ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="rst", direction=PortDirection.IN),
    Port(name="fast_clk", direction=PortDirection.IN),
]

default_clk_dom = ClockDomain(
    name="default",
    clock=ReferencedPort.external(external_ports[0]),
)

fast_clk_dom = ClockDomain(
    name="fast",
    clock=ReferencedPort.external(external_ports[2]),
)

default_rst_dom = ResetDomain(
    name="default",
    reset=ReferencedPort.external(external_ports[1]),
    polarity=ResetPolarity.ACTIVE_HIGH,
)

streamer = ModuleInstance(
    name="streamer",
    module=axis_clk_streamer,
    clocks={axis_clk_streamer.clocks[0]._id: fast_clk_dom},
    resets={axis_clk_streamer.resets[0]._id: default_rst_dom},
)
receiver = ModuleInstance(
    name="receiver",
    module=axis_clk_receiver,
    clocks={axis_clk_receiver.clocks[0]._id: default_clk_dom},
    resets={axis_clk_receiver.resets[0]._id: default_rst_dom},
)
cdc = ModuleInstance(
    name="cdc",
    module=axis_cdc,
    clocks={
        axis_cdc.clocks[0]._id: fast_clk_dom,
        axis_cdc.clocks[1]._id: default_clk_dom,
    },
    resets={axis_cdc.resets[0]._id: default_rst_dom},
)

module = Module(
    id=Identifier(name="top"),
    ports=external_ports,
    design=Design(
        components=[streamer, receiver, cdc],
        clock_domains=[default_clk_dom, fast_clk_dom],
        reset_domains=[default_rst_dom],
        connections=[
            InterfaceConnection(
                source=ReferencedInterface(instance=cdc, io=axis_cdc.interfaces[0]),
                target=ReferencedInterface(instance=streamer, io=axis_clk_streamer.interfaces[0]),
            ),
            InterfaceConnection(
                source=ReferencedInterface(instance=cdc, io=axis_cdc.interfaces[1]),
                target=ReferencedInterface(instance=receiver, io=axis_clk_receiver.interfaces[0]),
            ),
        ],
    ),
)

# TODO: This isn't the right place to do this...
assert module.design
module.design.lower_domains()
