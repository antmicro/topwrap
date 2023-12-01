# amaranth: UnusedElaboratable=no

# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Union

import pytest
from amaranth import *
from amaranth.hdl.ast import Assign
from amaranth.lib.wiring import Component, In, Out, Signature

from fpga_topwrap.amaranth_helpers import DIR_IN, DIR_OUT, WrapperPort
from fpga_topwrap.elaboratable_wrapper import ElaboratableWrapper, SignalMapping


@pytest.fixture
def elaboratable_name() -> str:
    return "test_elaboratable"


@pytest.fixture
def stream_signature() -> Signature:
    return Signature(
        {
            "data": Out(16),
            "valid": Out(1),
            "ready": In(1),
        }
    )


@pytest.fixture
def region_signature() -> Signature:
    return Signature(
        {
            "start": In(32),
            "end": In(32),
        }
    )


@pytest.fixture
def nested_signature(stream_signature: Signature, region_signature: Signature) -> Signature:
    return Signature(
        {
            "o": Out(stream_signature),
            "i": In(Signature({"meta": Out(4), "ok": In(1), "region": Out(region_signature)})),
        }
    )


@pytest.fixture
def nested_signature_mapping() -> SignalMapping:
    # Note: if parent Signature is marked as "In" then direction of its children
    # is flipped. This is consistent with Amaranth's convention, see:
    # https://amaranth-lang.org/rfcs/0002-interfaces.html#guide-level-explanation
    return {
        "o": {
            "data": WrapperPort(
                bounds=[15, 0, 15, 0],
                name="o_data",
                internal_name="data",
                interface_name="o",
                direction=DIR_OUT,
            ),
            "valid": WrapperPort(
                bounds=[0, 0, 0, 0],
                name="o_valid",
                internal_name="valid",
                interface_name="o",
                direction=DIR_OUT,
            ),
            "ready": WrapperPort(
                bounds=[0, 0, 0, 0],
                name="o_ready",
                internal_name="ready",
                interface_name="o",
                direction=DIR_IN,
            ),
        },
        "i": {
            "meta": WrapperPort(
                bounds=[3, 0, 3, 0],
                name="i_meta",
                internal_name="meta",
                interface_name="i",
                direction=DIR_IN,
            ),
            "ok": WrapperPort(
                bounds=[0, 0, 0, 0],
                name="i_ok",
                internal_name="ok",
                interface_name="i",
                direction=DIR_OUT,
            ),
            "region": {
                "start": WrapperPort(
                    bounds=[31, 0, 31, 0],
                    name="i_region_start",
                    internal_name="start",
                    interface_name="i_region",
                    direction=DIR_OUT,
                ),
                "end": WrapperPort(
                    bounds=[31, 0, 31, 0],
                    name="i_region_end",
                    internal_name="end",
                    interface_name="i_region",
                    direction=DIR_OUT,
                ),
            },
        },
    }


@pytest.fixture
def flattened_nested_signature_mapping() -> list[WrapperPort]:
    return [
        WrapperPort(
            bounds=[15, 0, 15, 0],
            name="o_data",
            internal_name="data",
            interface_name="o",
            direction=DIR_OUT,
        ),
        WrapperPort(
            bounds=[0, 0, 0, 0],
            name="o_valid",
            internal_name="valid",
            interface_name="o",
            direction=DIR_OUT,
        ),
        WrapperPort(
            bounds=[0, 0, 0, 0],
            name="o_ready",
            internal_name="ready",
            interface_name="o",
            direction=DIR_IN,
        ),
        WrapperPort(
            bounds=[3, 0, 3, 0],
            name="i_meta",
            internal_name="meta",
            interface_name="i",
            direction=DIR_IN,
        ),
        WrapperPort(
            bounds=[0, 0, 0, 0],
            name="i_ok",
            internal_name="ok",
            interface_name="i",
            direction=DIR_OUT,
        ),
        WrapperPort(
            bounds=[31, 0, 31, 0],
            name="i_region_start",
            internal_name="start",
            interface_name="i_region",
            direction=DIR_OUT,
        ),
        WrapperPort(
            bounds=[31, 0, 31, 0],
            name="i_region_end",
            internal_name="end",
            interface_name="i_region",
            direction=DIR_OUT,
        ),
    ]


@pytest.fixture
def elaboratable(nested_signature: Signature) -> Elaboratable:
    class TestModule(Component):
        def __init__(self):
            super().__init__(signature=nested_signature)

        def elaborate(self):
            m = Module()
            return m

    return TestModule()


@pytest.fixture
def elaboratable_wrapper(elaboratable_name: str, elaboratable: Elaboratable) -> ElaboratableWrapper:
    return ElaboratableWrapper(elaboratable_name, elaboratable)


@pytest.fixture
def make_cached_wrapper_port1(elaboratable_wrapper: ElaboratableWrapper) -> WrapperPort:
    return lambda: elaboratable_wrapper._cached_wrapper(
        port_width=12,
        port_flow=In,
        name="wrapper_port1",
        port_name="port1",
        iface_name="sample_iface",
    )


@pytest.fixture
def make_cached_wrapper_port2(elaboratable_wrapper: ElaboratableWrapper) -> WrapperPort:
    return lambda: elaboratable_wrapper._cached_wrapper(
        port_width=13,
        port_flow=In,
        name="wrapper_port2",
        port_name="port2",
        iface_name="sample_iface",
    )


@pytest.fixture
def clock_domain_signals(elaboratable_wrapper: ElaboratableWrapper) -> SignalMapping:
    return {"clk": elaboratable_wrapper.clk, "rst": elaboratable_wrapper.rst}


@pytest.fixture
def interface_connections(
    elaboratable: Elaboratable, nested_signature_mapping: SignalMapping
) -> list[tuple[Signal, Signal]]:
    m = elaboratable
    d = nested_signature_mapping
    return [
        (d["o"]["data"], m.o.data),
        (d["o"]["valid"], m.o.valid),
        (m.o.ready, d["o"]["ready"]),
        (m.i.meta, d["i"]["meta"]),
        (d["i"]["ok"], m.i.ok),
        (d["i"]["region"]["start"], m.i.region.start),
        (d["i"]["region"]["end"], m.i.region.end),
    ]


def wrapper_port_eq(p1: WrapperPort, p2: WrapperPort) -> bool:
    for attr in ["bounds", "name", "internal_name", "interface_name", "direction"]:
        if getattr(p1, attr) != getattr(p2, attr):
            return False
    return True


def signal_mapping_elem_eq(
    v1: Union[SignalMapping, WrapperPort], v2: Union[SignalMapping, WrapperPort]
) -> bool:
    return (isinstance(v1, dict) and isinstance(v2, dict) and signal_mapping_eq(v1, v2)) or (
        isinstance(v1, WrapperPort) and isinstance(v2, WrapperPort) and wrapper_port_eq(v1, v2)
    )


def signal_mapping_eq(d1: SignalMapping, d2: SignalMapping) -> bool:
    if d1.keys() != d2.keys():
        return False

    for k, v1 in d1.items():
        v2 = d2[k]
        if not signal_mapping_elem_eq(v1, v2):
            return False
    return True


class TestElaboratableWrapper:
    def test_gather_signature_ports(
        self, elaboratable_wrapper: ElaboratableWrapper, nested_signature_mapping: SignalMapping
    ) -> None:
        sig = elaboratable_wrapper.elaboratable.signature
        sig_dict = elaboratable_wrapper._gather_signature_ports(sig)
        assert signal_mapping_eq(sig_dict, nested_signature_mapping)

    def test_flatten_hier(
        self,
        elaboratable_wrapper: ElaboratableWrapper,
        nested_signature_mapping: SignalMapping,
        flattened_nested_signature_mapping: list[WrapperPort],
    ) -> None:
        def ordering(p):
            return p.name

        flattened_hier = sorted(
            elaboratable_wrapper._flatten_hier(nested_signature_mapping), key=ordering
        )
        expected_hier = sorted(flattened_nested_signature_mapping, key=ordering)
        for port_test, port_expect in zip(flattened_hier, expected_hier):
            assert wrapper_port_eq(port_expect, port_test)

    def test_cached_wrapper(
        self,
        make_cached_wrapper_port1: Callable[[None], WrapperPort],
        make_cached_wrapper_port2: Callable[[None], WrapperPort],
    ) -> None:
        port1 = make_cached_wrapper_port1()
        port1_another = make_cached_wrapper_port1()
        port2 = make_cached_wrapper_port2()
        assert port1 is port1_another  # pointer equality
        assert not wrapper_port_eq(port1, port2)  # structural inequality

    def test_get_ports_hier(
        self,
        elaboratable_wrapper: ElaboratableWrapper,
        nested_signature_mapping: SignalMapping,
        clock_domain_signals: SignalMapping,
    ) -> None:
        hier_ports = elaboratable_wrapper.get_ports_hier()
        assert signal_mapping_eq(hier_ports, nested_signature_mapping | clock_domain_signals)

    def test_get_ports(
        self,
        elaboratable_wrapper: ElaboratableWrapper,
        flattened_nested_signature_mapping: list[WrapperPort],
        clock_domain_signals: SignalMapping,
    ) -> None:
        def ordering(p):
            return p.name

        ports = sorted(elaboratable_wrapper.get_ports(), key=ordering)
        expected_ports = sorted(
            flattened_nested_signature_mapping + list(clock_domain_signals.values()), key=ordering
        )
        for port_test, port_expect in zip(ports, expected_ports):
            assert wrapper_port_eq(port_expect, port_test)

    def test_connect_ports(
        self,
        elaboratable_wrapper: ElaboratableWrapper,
        nested_signature_mapping: SignalMapping,
        elaboratable: Elaboratable,
        interface_connections: list[tuple[Signal, Signal]],
    ) -> None:
        conns_test = sorted(
            elaboratable_wrapper._connect_ports(nested_signature_mapping, elaboratable),
            key=lambda conn: conn.lhs.name,
        )
        conns_expect = sorted(interface_connections, key=lambda conn: conn[0].name)
        for conn_test, conn_expect in zip(conns_test, conns_expect):
            lhs, rhs = conn_expect
            assert isinstance(conn_test, Assign)
            assert lhs is conn_test.lhs  # pointer equality
            assert rhs is conn_test.rhs  # pointer equality
