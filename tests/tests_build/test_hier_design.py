# amaranth: UnusedElaboratable=no

# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import itertools
from pathlib import Path

import pytest
from amaranth.hdl import ast
from yaml import Loader, load

from topwrap.design import generate_design
from topwrap.ipconnect import IPConnect
from topwrap.ipwrapper import IPWrapper


@pytest.fixture
def hier_design_yaml() -> Path:
    return Path("tests/data/data_build/hierarchy/design.yml")


@pytest.fixture
def hier_design(hier_design_yaml) -> dict:
    with open(hier_design_yaml, "r") as f:
        design = load(f, Loader=Loader)
    return design


@pytest.fixture
def counter_hier_name() -> str:
    return "counter_hier"


@pytest.fixture
def pwm_mod_name() -> str:
    return "pwm"


@pytest.fixture
def counter_mod_name() -> str:
    return "counter"


@pytest.fixture
def counter_hier_conns() -> list:
    return {
        "in_clk": "top_clk",
        "in_en": "sig_pwm",
        "top_cnt": "out_cnt",
    }


@pytest.fixture
def hier_design_ipconnect(hier_design) -> IPConnect:
    return generate_design(hier_design["ips"], hier_design["design"], hier_design["external"])


class TestHierarchyDesign:
    """Check whether the generated structure consisting of `IPConnect`, hierarchical `IPConnect`
    and `IPWrapper` objects is correct for the test design.
    """

    def test_hierarchy_structure(
        self, hier_design_ipconnect, counter_hier_name, pwm_mod_name, counter_mod_name
    ):
        # The top IPConnect has two components - `pwm` module and `counter_hier` hierarchy
        pwm_mod = hier_design_ipconnect._get_component_by_name(pwm_mod_name)
        counter_hier = hier_design_ipconnect._get_component_by_name(counter_hier_name)
        assert isinstance(pwm_mod, IPWrapper)
        assert isinstance(counter_hier, IPConnect)

        # `counter_hier` IPConnect has a single `IPConnect` object, which contains
        # a single `IPWrapper` object representing a `counter` module
        counter_mod = counter_hier._get_component_by_name(counter_mod_name)
        assert isinstance(counter_mod, IPWrapper)

    def test_connections_of_hierarchy(
        self, hier_design_ipconnect, counter_hier_name, counter_hier_conns
    ):
        """Check whether the connections from/to the `counter_hier` hierarchy have been
        created correctly. We should have:
        * `in_clk` incoming from the top module
        * `out_cnt` outgoing as external output of the top module
        * a wire between `sig_pwm` of pwm module and `in_en` of the hierarchy
        """
        # gather all ports from the ipconnect and all of its components
        name_sig = {
            sig.name: sig
            for sig in itertools.chain.from_iterable(
                [hier_design_ipconnect.get_ports()]
                + [comp.get_ports() for comp in hier_design_ipconnect._components.values()]
            )
        }

        conn_count = 0
        for conn in hier_design_ipconnect._connections:
            assert isinstance(conn, ast.Assign)
            lhs = conn.lhs
            rhs = conn.rhs

            if lhs.name in counter_hier_conns:
                assert rhs.name == counter_hier_conns[lhs.name]
                assert name_sig[lhs.name] is lhs
                assert name_sig[rhs.name] is rhs
                conn_count += 1
        # make sure we've checked connections of all signals
        assert conn_count == len(counter_hier_conns)
