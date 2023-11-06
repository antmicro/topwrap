# amaranth: UnusedElaboratable=no

# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from yaml import Loader, load

from fpga_topwrap.design import generate_design
from fpga_topwrap.hierarchy_wrapper import HierarchyWrapper
from fpga_topwrap.ipconnect import IPConnect
from fpga_topwrap.ipwrapper import IPWrapper


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
    return ["in_en_sig_pwm", "top_clk", "top_cnt"]


@pytest.fixture
def hier_design_ipconnect(hier_design) -> IPConnect:
    return generate_design(hier_design["ips"], hier_design["design"], hier_design["external"])


class TestHierarchyDesign:
    """Check whether the generated structure consisting of `IPConnect`, `HierarchyWrapper`
    and `IPWrapper` objects is correct for the test design.
    """

    def test_hierarchy_structure(
        self, hier_design_ipconnect, counter_hier_name, pwm_mod_name, counter_mod_name
    ):
        # The top IPConnect has two components - `pwm` module and `counter_hier` hierarchy
        pwm_mod = hier_design_ipconnect._get_component_by_name(pwm_mod_name)
        counter_hier = hier_design_ipconnect._get_component_by_name(counter_hier_name)
        assert isinstance(pwm_mod, IPWrapper)
        assert isinstance(counter_hier, HierarchyWrapper)

        # `counter_hier` HierarchyWrapper has a single `IPConnect` object, which contains
        # a single `IPWrapper` object representing a `counter` module
        assert isinstance(counter_hier.ipc, IPConnect)
        counter_mod = counter_hier.ipc._get_component_by_name(counter_mod_name)
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
        conns = getattr(hier_design_ipconnect, counter_hier_name)
        assert sorted([sig.name for sig in conns.values()]) == counter_hier_conns
