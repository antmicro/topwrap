import dataclasses
import re
from pathlib import Path
from typing import List, Set

import pytest

from topwrap.hdl_parsers_utils import PortDefinition, PortDirection
from topwrap.interface import (
    IfacePortSpecification,
    InterfaceDefinition,
    InterfaceDefinitionSignals,
    InterfaceMode,
    InterfaceSignalType,
    get_interfaces,
)
from topwrap.interface_grouper import (
    BasicModeDeducer,
    EmptyGrouper,
    GrouperByAttribute,
    GrouperByPrefix,
    GrouperByPrefixAuto,
    Interface4StageGrouper,
    InterfaceGrouper,
    InterfaceMatchGroupScorer,
    RegexInterfaceMatcher,
)

from .parse_common import (
    AXI_AXIL_ADAPTER_IFACES,
    AXI_AXIL_ADAPTER_MASTER_PORTS,
    AXI_AXIL_ADAPTER_PORTS,
    AXI_AXIL_ADAPTER_SLAVE_PORTS,
    AXI_DISPCTRL_IFACES,
    AXI_DISPCTRL_PORTS,
)


@pytest.fixture
def foo_a_data_in() -> PortDefinition:
    return PortDefinition(
        name="foo_a_data_in",
        upper_bound="3",
        lower_bound="2",
        direction=PortDirection.IN,
    )


@pytest.fixture
def foo_a_data_out() -> PortDefinition:
    return PortDefinition(
        name="foo_a_data_out",
        upper_bound="DOUT_WIDTH",
        lower_bound="0",
        direction=PortDirection.OUT,
    )


@pytest.fixture
def foo_a_valid() -> PortDefinition:
    return PortDefinition(
        name="foo_a_valid",
        upper_bound="42",
        lower_bound="26",
        direction=PortDirection.IN,
    )


@pytest.fixture
def foo_a_ready() -> PortDefinition:
    return PortDefinition(
        name="foo_a_ready",
        upper_bound="1",
        lower_bound="0",
        direction=PortDirection.OUT,
    )


@pytest.fixture
def foo_a_ports(
    foo_a_data_in: PortDefinition,
    foo_a_data_out: PortDefinition,
    foo_a_valid: PortDefinition,
    foo_a_ready: PortDefinition,
) -> List[PortDefinition]:
    return [foo_a_data_in, foo_a_data_out, foo_a_valid, foo_a_ready]


@pytest.fixture
def foo_b_ports() -> List[PortDefinition]:
    return [
        PortDefinition(
            name="foo_b_data_in",
            upper_bound="3",
            lower_bound="2",
            direction=PortDirection.IN,
        ),
        PortDefinition(
            name="foo_b_data_out",
            upper_bound="DOUT_WIDTH",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        PortDefinition(
            name="foo_b_valid",
            upper_bound="42",
            lower_bound="26",
            direction=PortDirection.IN,
        ),
        PortDefinition(
            name="foo_b_ready",
            upper_bound="1",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
    ]


@pytest.fixture
def free_ports() -> List[PortDefinition]:
    return [
        PortDefinition(
            name="clk",
            upper_bound="1",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        PortDefinition(
            name="rst",
            upper_bound="1",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
    ]


@pytest.fixture
def rtl_ports(
    foo_a_ports: List[PortDefinition],
    foo_b_ports: List[PortDefinition],
    free_ports: List[PortDefinition],
) -> Set[PortDefinition]:
    return set(foo_a_ports + foo_b_ports + free_ports)


@pytest.fixture
def iface_data_in() -> IfacePortSpecification:
    return IfacePortSpecification(
        name="data_in",
        regexp=re.compile("data_in"),
        direction=PortDirection.IN,
        type=InterfaceSignalType.REQUIRED,
    )


@pytest.fixture
def iface_data_out() -> IfacePortSpecification:
    return IfacePortSpecification(
        name="data_out",
        regexp=re.compile("data_out"),
        direction=PortDirection.OUT,
        type=InterfaceSignalType.REQUIRED,
    )


@pytest.fixture
def iface_valid() -> IfacePortSpecification:
    return IfacePortSpecification(
        name="valid",
        regexp=re.compile("valid"),
        direction=PortDirection.IN,
        type=InterfaceSignalType.REQUIRED,
    )


@pytest.fixture
def iface_ready() -> IfacePortSpecification:
    return IfacePortSpecification(
        name="ready",
        regexp=re.compile("ready"),
        direction=PortDirection.OUT,
        type=InterfaceSignalType.REQUIRED,
    )


@pytest.fixture
def foo_interface_ports(
    iface_data_in: IfacePortSpecification,
    iface_data_out: IfacePortSpecification,
    iface_valid: IfacePortSpecification,
    iface_ready: IfacePortSpecification,
) -> List[IfacePortSpecification]:
    return [iface_data_in, iface_data_out, iface_valid, iface_ready]


@pytest.fixture
def foo_interface(foo_interface_ports: List[IfacePortSpecification]) -> InterfaceDefinition:
    return InterfaceDefinition(
        name="foo_iface",
        port_prefix="foo",
        signals=InterfaceDefinitionSignals.from_flat(foo_interface_ports),
    )


class TestSignalGroupers:
    @pytest.fixture
    def hdl_file(self) -> Path:
        return Path("tests/data/data_parse/axi_axil_adapter.v")

    def test_empty_grouper(self, rtl_ports: Set[PortDefinition]):
        assert EmptyGrouper().group(rtl_ports) == {}

    def test_grouper_by_prefix(
        self,
        rtl_ports: Set[PortDefinition],
        foo_a_ports: List[PortDefinition],
        foo_b_ports: List[PortDefinition],
    ):
        prefix_grouper = GrouperByPrefix(["foo"])
        assert prefix_grouper.group(rtl_ports) == {"foo": set(foo_a_ports + foo_b_ports)}

        prefix_grouper = GrouperByPrefix(["foo_a", "foo_b"])
        assert prefix_grouper.group(rtl_ports) == {
            "foo_a": set(foo_a_ports),
            "foo_b": set(foo_b_ports),
        }

    def test_grouper_by_prefix_auto(
        self,
        rtl_ports: Set[PortDefinition],
        foo_a_ports: List[PortDefinition],
        foo_b_ports: List[PortDefinition],
    ):
        autoprefix_grouper = GrouperByPrefixAuto(min_prefix_occurences=4)
        assert autoprefix_grouper.group(rtl_ports) == {
            "foo_a": set(foo_a_ports),
            "foo_b": set(foo_b_ports),
        }
        autoprefix_grouper = GrouperByPrefixAuto(min_prefix_occurences=5)
        assert autoprefix_grouper.group(rtl_ports) == {"foo": set(foo_a_ports + foo_b_ports)}
        autoprefix_grouper = GrouperByPrefixAuto(min_prefix_occurences=9)
        assert autoprefix_grouper.group(rtl_ports) == {}

    def test_grouper_by_attribute(self, hdl_file: Path):
        attr_grouper = GrouperByAttribute(hdl_file)
        assert attr_grouper.group(AXI_AXIL_ADAPTER_PORTS) == {
            "axi_slave": set(AXI_AXIL_ADAPTER_SLAVE_PORTS),
            "axi_master": set(AXI_AXIL_ADAPTER_MASTER_PORTS),
        }


class TestInterfaceMatchers:
    def test_regex_matcher_full_match(
        self, foo_a_ports: List[PortDefinition], foo_interface_ports: List[IfacePortSpecification]
    ):
        regex_matcher = RegexInterfaceMatcher()
        iface_match = regex_matcher.match(set(foo_interface_ports), set(foo_a_ports))
        for rtl_port, iface_port in zip(foo_a_ports, foo_interface_ports):
            assert iface_match[iface_port] == rtl_port

    def test_regex_matcher_partial_match(
        self,
        foo_interface_ports: List[IfacePortSpecification],
        iface_data_in: IfacePortSpecification,
        iface_data_out: IfacePortSpecification,
        iface_valid: IfacePortSpecification,
        foo_a_data_in: PortDefinition,
        foo_a_data_out: PortDefinition,
        foo_a_valid: PortDefinition,
    ):
        regex_matcher = RegexInterfaceMatcher()
        # replace last element (nominally foo_a_ready) with port that shouldn't match
        foo_a_ports = [
            foo_a_data_in,
            foo_a_data_out,
            foo_a_valid,
            PortDefinition(
                name="not_matching_name",
                upper_bound="23",
                lower_bound="0",
                direction=PortDirection.IN,
            ),
        ]
        iface_match = regex_matcher.match(set(foo_interface_ports), set(foo_a_ports))

        # should only match 3 signals
        assert len(iface_match) == 3
        assert iface_match[iface_data_in] == foo_a_data_in
        assert iface_match[iface_data_out] == foo_a_data_out
        assert iface_match[iface_valid] == foo_a_valid

    def test_regex_matcher_empty_match(
        self, free_ports: List[PortDefinition], foo_interface_ports: List[IfacePortSpecification]
    ):
        regex_matcher = RegexInterfaceMatcher()
        iface_match = regex_matcher.match(set(foo_interface_ports), set(free_ports))
        # no ports should get matched since they don't conform to any regex
        assert len(iface_match) == 0


class TestInterfaceScorers:
    # Testing InterfaceMatchGroupScorer tests several invariants that must hold
    # under default config values. ">"/">="/"==" should be read as
    # "must have a greater/greater or equal/equal score than".
    # Partial matching means matching where some rtl signals haven't been matched to interface
    # signals, full matching means matching where all have been matched.
    #
    # Tested invariants:
    # inv. 1. full matching with N+1 signals matched (same type) == full matching with N signals matched (same type)
    # inv. 2. full matching with N signals matched (same type) > partial matching with N signals matched (same type)
    # inv. 3. partial matching with N+1 signals matched (same type) > partial matching with N signals matched (same type)
    # inv. 4.   full matching with N+1 required, M+1 optional signals
    #         >= full matching with N+1 optional, M   optional signals
    #         >= full matching with N   required, M+1 optional signals
    #         >= full matching with N   required, M   optional signals
    def test_group_scorer_inv123(
        self, foo_a_ports: List[PortDefinition], foo_interface: InterfaceDefinition
    ):
        group_scorer = InterfaceMatchGroupScorer()
        matcher = RegexInterfaceMatcher()

        # 4 signals
        foo_interface4 = foo_interface
        # 4 signals, 4 matched
        fullmatch4 = matcher.match(set(foo_interface4.signals.flat), set(foo_a_ports))
        # 3 signals, 3 matched
        fullmatch3 = matcher.match(set(foo_interface4.signals.flat[1:]), set(foo_a_ports[1:]))
        # 4 signals, 3 matched
        partialmatch4 = matcher.match(set(foo_interface4.signals.flat), set(foo_a_ports[1:]))

        # 3 signals
        foo_interface3 = dataclasses.replace(
            foo_interface4,
            signals=InterfaceDefinitionSignals.from_flat(foo_interface4.signals.flat[1:]),
        )
        # 3 signals, 2 matched
        partialmatch3 = matcher.match(set(foo_interface3.signals.flat), set(foo_a_ports[2:]))

        # invariant 1.
        assert group_scorer.score(foo_interface4, foo_a_ports, fullmatch4) == group_scorer.score(
            foo_interface3, foo_a_ports[1:], fullmatch3
        )
        # invariant 2.
        assert group_scorer.score(foo_interface4, foo_a_ports, fullmatch4) > group_scorer.score(
            foo_interface4, foo_a_ports, partialmatch4
        )
        # invariant 3.
        assert group_scorer.score(foo_interface4, foo_a_ports, partialmatch4) > group_scorer.score(
            foo_interface3, foo_a_ports[1:], partialmatch3
        )

    def test_group_scorer_inv4(
        self,
        iface_data_in: IfacePortSpecification,
        iface_data_out: IfacePortSpecification,
        iface_valid: IfacePortSpecification,
        iface_ready: IfacePortSpecification,
        foo_a_data_in: PortDefinition,
        foo_a_data_out: PortDefinition,
        foo_a_valid: PortDefinition,
        foo_a_ready: PortDefinition,
        foo_interface: InterfaceDefinition,
    ):
        def make_optional(port: IfacePortSpecification) -> IfacePortSpecification:
            return dataclasses.replace(port, type=InterfaceSignalType.OPTIONAL)

        group_scorer = InterfaceMatchGroupScorer()

        n1_req_m1_opt = {
            iface_data_in: foo_a_data_in,
            iface_data_out: foo_a_data_out,
            make_optional(iface_valid): foo_a_valid,
            make_optional(iface_ready): foo_a_ready,
        }
        iface_n1_m1 = dataclasses.replace(
            foo_interface, signals=InterfaceDefinitionSignals.from_flat(list(n1_req_m1_opt.keys()))
        )
        ports_n1_m1 = set(n1_req_m1_opt.values())
        score_n1_m1 = group_scorer.score(iface_n1_m1, ports_n1_m1, n1_req_m1_opt)

        n1_req_m_opt = {
            iface_data_in: foo_a_data_in,
            iface_data_out: foo_a_data_out,
            make_optional(iface_valid): foo_a_valid,
        }
        iface_n1_m = dataclasses.replace(
            foo_interface, signals=InterfaceDefinitionSignals.from_flat(list(n1_req_m_opt.keys()))
        )
        ports_n1_m = set(n1_req_m_opt.values())
        score_n1_m = group_scorer.score(iface_n1_m, ports_n1_m, n1_req_m_opt)

        n_req_m1_opt = {
            iface_data_in: foo_a_data_in,
            iface_data_out: foo_a_data_out,
            make_optional(iface_valid): foo_a_valid,
        }
        iface_n_m1 = dataclasses.replace(
            foo_interface, signals=InterfaceDefinitionSignals.from_flat(list(n_req_m1_opt.keys()))
        )
        ports_n_m1 = set(n_req_m1_opt.values())
        score_n_m1 = group_scorer.score(iface_n_m1, ports_n_m1, n_req_m1_opt)

        n_req_m_opt = {
            iface_data_in: foo_a_data_in,
            make_optional(iface_data_out): foo_a_data_out,
        }
        iface_n_m = dataclasses.replace(
            foo_interface, signals=InterfaceDefinitionSignals.from_flat(list(n_req_m_opt.keys()))
        )
        ports_n_m = set(n_req_m_opt.values())
        score_n_m = group_scorer.score(iface_n_m, ports_n_m, n_req_m_opt)

        # Under current implementation all scores in invariant 4. are equal to not favorize
        # interfaces with more signals, as they could in theory have a greater score without
        # matching all signals than an interface with less signals but matching all of them
        # (we prefer the latter, but in a different implementation the former might be desirable).
        assert score_n1_m1 >= score_n1_m >= score_n_m1 >= score_n_m


class TestModeDeducers:
    def test_basic_deducer(
        self, foo_interface: InterfaceDefinition, foo_a_ports: List[PortDefinition]
    ):
        def invert_direction(port: PortDefinition) -> PortDefinition:
            return dataclasses.replace(
                port,
                direction=(
                    PortDirection.IN if port.direction == PortDirection.OUT else PortDirection.IN
                ),
            )

        basic_deducer = BasicModeDeducer()
        matcher = RegexInterfaceMatcher()

        # if rtl ports directions' match iface ports directions' this it's a master
        # since convention is to describe directions in an interface from the master's perspective
        matching_master = matcher.match(set(foo_interface.signals.flat), foo_a_ports)
        assert basic_deducer.deduce_mode(foo_interface, matching_master) == InterfaceMode.MASTER

        # conversely if the directions are inverted it's a slave
        matching_slave = matcher.match(
            set(foo_interface.signals.flat), set(map(invert_direction, foo_a_ports))
        )
        assert basic_deducer.deduce_mode(foo_interface, matching_slave) == InterfaceMode.SLAVE

        # negative test - empty matching
        assert basic_deducer.deduce_mode(foo_interface, {}) == InterfaceMode.UNSPECIFIED


class TestInterfaceGroupers:
    @pytest.fixture
    def grouper(self):
        return Interface4StageGrouper(
            get_interfaces(),
            GrouperByPrefixAuto(),
            RegexInterfaceMatcher(),
            InterfaceMatchGroupScorer(),
            BasicModeDeducer(),
        )

    def test_axi_axilite(self, grouper: InterfaceGrouper):
        expected = AXI_AXIL_ADAPTER_IFACES
        got = grouper.group_to_interfaces(AXI_AXIL_ADAPTER_PORTS)
        # can't compare those directly as they can't be turned into sets nor sorted since they contain dicts
        # so we make sure they're equal in length and check that they contain equivalent elements
        assert len(expected) == len(got)
        for item in got:
            assert item in expected

    def test_axis(self, grouper: InterfaceGrouper):
        # contains axi-stream interfaces
        expected = AXI_DISPCTRL_IFACES
        got = grouper.group_to_interfaces(AXI_DISPCTRL_PORTS)
        assert len(expected) == len(got)
        for item in got:
            assert item in expected
