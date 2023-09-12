# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest

from yaml import load, Loader
from pathlib import Path
from fpga_topwrap.design import generate_design
from fpga_topwrap.ipconnect import IPConnect
from fpga_topwrap.ipwrapper import IPWrapper
from fpga_topwrap.hierarchy_wrapper import HierarchyWrapper
from fpga_topwrap.nm_helper import PortDirection, DIR_IN, DIR_OUT


@pytest.fixture
def hier_design_yaml() -> Path:
    return Path("tests/data/data_build/hierarchy/design.yml")

@pytest.fixture
def hier_design(hier_design_yaml) -> dict:
    with open(hier_design_yaml, "r") as f:
        design = load(f, Loader=Loader)
    return design

@pytest.fixture
def hier_top_ipconnect(hier_design) -> IPConnect:
    design = hier_design["design"] if "design" in hier_design.keys() else dict()
    external = hier_design["external"] if "external" in hier_design.keys() else dict()
    return generate_design(hier_design["ips"], design, external)

def _get_inner_ipconnect(top_ipconnect: IPConnect, hier_name: str) -> IPConnect:
    """Return IPConnect object of Hierarchy Wrapper belonging to `top_ipconnect`.

    This function must be used on condition that `top_ipconnect` contains `hier_name`
    component, which is a HierarchyWrapper
    """
    return top_ipconnect._get_component_by_name(hier_name).ipc

# Expected hierarchies and modules names:

@pytest.fixture
def counter_hier_name() -> str:
    return "counter_hier"

@pytest.fixture
def counter_mod_name() -> str:
    return "counter"

@pytest.fixture
def pwm_mod_name() -> str:
    return "pwm"

# Expected ports of modules and hierarchies and their widths:

@pytest.fixture
def toplevel_ports() -> list:
    return [("top_clk", 1), ("top_compare", 32), ("top_cnt", 16)]

@pytest.fixture
def pwm_ports() -> list:
    return [("clk", 1), ("compare", 32), ("sig_pwm", 1)]

@pytest.fixture
def counter_hierarchy_ports() -> list:
    return [("out_cnt", 16), ("in_en", 1), ("in_clk", 1)]

# Helper functions:

def _get_second_level_hier_by_name(
    hier_top_ipconnect: IPConnect, top_hier_name: str, sec_lvl_hier_name: str
):
    """Helper function to get second-level hierarchy (`pwm_hier` or `counters_hier`)"""
    top_hier_ipc = _get_inner_ipconnect(hier_top_ipconnect, top_hier_name)
    return _get_inner_ipconnect(top_hier_ipc, sec_lvl_hier_name)


def _get_ip_ports_by_dir(ipcw, dir: PortDirection) -> list:
    return list(filter(lambda port: port.direction == dir, ipcw.get_ports()))


class TestHierarchyDesign:
    # Tests for top-level IPConnect:
    def test_external_ports(self, hier_top_ipconnect, toplevel_ports):
        """Check if top module has all the defined external ports"""
        assert len(_get_ip_ports_by_dir(hier_top_ipconnect, DIR_IN)) == 2
        assert len(_get_ip_ports_by_dir(hier_top_ipconnect, DIR_OUT)) == 1
        assert sorted([port.name for port in hier_top_ipconnect.get_ports()]) == toplevel_ports

    def test_components(self, hier_top_ipconnect, top_hier_name):
        """Check if top-level IPConnect has the defined top-hierarchy component"""
        assert len(hier_top_ipconnect._components) == 1
        assert isinstance(
            hier_top_ipconnect._get_component_by_name(top_hier_name), HierarchyWrapper
        )

    # Tests for top hierarchy:
    def test_top_hierarchy_ports(self, hier_top_ipconnect, top_hier_name, top_hierarchy_ports):
        """Check if top-hierarchy has all the defined external ports"""
        top_hier_ipc = _get_inner_ipconnect(hier_top_ipconnect, top_hier_name)
        assert len(_get_ip_ports_by_dir(top_hier_ipc, DIR_IN)) == 2
        assert len(_get_ip_ports_by_dir(top_hier_ipc, DIR_OUT)) == 1
        assert sorted([port.name for port in top_hier_ipc.get_ports()]) == top_hierarchy_ports


    # Test for pwm module:
    def test_pwm_module_ports(
        self, hier_top_ipconnect, top_hier_name, pwm_hier_name, pwm_mod_name, pwm_module_ports
    ):
        """Check pwm module ports - check their directions, names and widths"""
        pwm_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, pwm_hier_name
        )
        pwm_ipw = pwm_hier_ipc._get_component_by_name(pwm_mod_name)
        assert len(_get_ip_ports_by_dir(pwm_hier_ipc, DIR_IN)) == 2
        assert len(_get_ip_ports_by_dir(pwm_hier_ipc, DIR_OUT)) == 1
        assert sorted([(port.name, len(port)) for port in pwm_ipw.get_ports()]) == pwm_module_ports

    # Tests for counters hierarchy:
    def test_counters_hierarchy_ports(
        self, hier_top_ipconnect, top_hier_name, counters_hier_name, counters_hierarchy_ports
    ):
        """Check if counters hierarchy (which wraps two counters) has all the defined ports"""
        cnt_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, counters_hier_name
        )
        assert len(_get_ip_ports_by_dir(cnt_hier_ipc, DIR_IN)) == 1
        assert len(_get_ip_ports_by_dir(cnt_hier_ipc, DIR_OUT)) == 2
        assert sorted([port.name for port in cnt_hier_ipc.get_ports()]) == counters_hierarchy_ports

    def test_counters_hierarchy_components(
        self,
        hier_top_ipconnect,
        top_hier_name,
        counters_hier_name,
        counter_up_mod_name,
        counter_down_mod_name,
    ):
        """Check if counters hierarchy contains 2 modules - up-counter and down-counter"""
        cnt_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, counters_hier_name
        )
        assert len(cnt_hier_ipc._components) == 2
        assert isinstance(cnt_hier_ipc._get_component_by_name(counter_up_mod_name), IPWrapper)
        assert isinstance(cnt_hier_ipc._get_component_by_name(counter_down_mod_name), IPWrapper)

    # Test for up-counter module:
    def test_counter_up_module_ports(
        self,
        hier_top_ipconnect,
        top_hier_name,
        counters_hier_name,
        counter_up_mod_name,
        counter_up_module_ports,
    ):
        """Check counter_up module ports - check their directions, names and widths"""
        cnt_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, counters_hier_name
        )
        cnt_ipw = cnt_hier_ipc._get_component_by_name(counter_up_mod_name)
        assert len(_get_ip_ports_by_dir(cnt_ipw, DIR_IN)) == 1
        assert len(_get_ip_ports_by_dir(cnt_ipw, DIR_OUT)) == 1
        assert (
            sorted([(port.name, len(port)) for port in cnt_ipw.get_ports()])
            == counter_up_module_ports
        )
