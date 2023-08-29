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
    return Path("tests/data/hierarchy/design.yml")


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
def top_hier_name() -> str:
    return "top_hierarchy"


@pytest.fixture
def counters_hier_name() -> str:
    return "counters_hier"


@pytest.fixture
def counter_up_mod_name() -> str:
    return "counter_up"


@pytest.fixture
def counter_down_mod_name() -> str:
    return "counter_down"


@pytest.fixture
def pwm_hier_name() -> str:
    return "pwm_hier"


@pytest.fixture
def pwm_mod_name() -> str:
    return "pwm"


@pytest.fixture
def select_mod_name() -> str:
    return "sig_select"


# Expected hierarchies ports names:


@pytest.fixture
def toplevel_ports() -> list:
    return ["top_clk", "top_cnt", "top_compare"]


@pytest.fixture
def top_hierarchy_ports() -> list:
    return ["clk", "cnt", "compare"]


@pytest.fixture
def pwm_hierarchy_ports() -> list:
    return ["pwm_clk", "pwm_compare", "sig_pwm"]


@pytest.fixture
def counters_hierarchy_ports() -> list:
    return ["cnt_down", "cnt_up", "in_clk"]


# Expected modules port names and their widths:


@pytest.fixture
def pwm_module_ports() -> list:
    return [("clk", 1), ("compare", 32), ("sig_pwm", 1)]


@pytest.fixture
def counter_up_module_ports() -> list:
    return [("clk", 1), ("cnt", 16)]


@pytest.fixture
def counter_down_module_ports() -> list:
    return [("clk", 1), ("cnt", 16)]


@pytest.fixture
def select_module_ports() -> list:
    return [("out_sig", 16), ("sig1", 16), ("sig2", 16), ("sig_choose", 1)]


# Expected number of connections inside hierarchies


@pytest.fixture
def top_hierarchy_connections() -> int:
    """Return number of defined connections inside top_hierachy. This includes:

    * 3 wires for pwm hierarchy (2 in + 1 out)
    * 3 wires for counters hierarchy (1 in + 2 out)
    * 4 wires for sig_select module (3 in + 1 out)
    """
    return 10


# Helper functions:


def _get_second_level_hier_by_name(
    hier_top_ipconnect: IPConnect, top_hier_name: str, sec_lvl_hier_name: str
):
    """Helper function to get second-level hierarchy (`pwm_hier` or `counters_hier`)"""
    top_hier_ipc = _get_inner_ipconnect(hier_top_ipconnect, top_hier_name)
    return _get_inner_ipconnect(top_hier_ipc, sec_lvl_hier_name)


def _get_ip_ports_by_dir(ipcw: IPConnect | IPWrapper, dir: PortDirection) -> list:
    return list(filter(lambda port: port.direction == dir, ipcw.get_ports()))


class TestHierarchyDesign:
    # Tests for top-level IPConnect:
    def test_external_ports(self, hier_top_ipconnect, toplevel_ports):
        """Check if top module has all the defined external ports"""
        assert len(_get_ip_ports_by_dir(hier_top_ipconnect, DIR_IN)) == 2
        assert len(_get_ip_ports_by_dir(hier_top_ipconnect, DIR_OUT)) == 1
        assert sorted([port.name for port in hier_top_ipconnect.get_ports()]) == toplevel_ports

    def test_component(self, hier_top_ipconnect, top_hier_name):
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

    def test_top_hierarchy_components(
        self, hier_top_ipconnect, top_hier_name, pwm_hier_name, counters_hier_name, select_mod_name
    ):
        """Check if top-hierarchy contains all the defined sub-hierarchies and modules:

        * pwm_hier hierarchy (which wraps only pwm module)
        * counters_hier hierarchy (which wraps 2 counter modules)
        * sig_select module
        """
        top_hier_ipc = _get_inner_ipconnect(hier_top_ipconnect, top_hier_name)
        assert len(top_hier_ipc._components) == 3
        assert isinstance(top_hier_ipc._get_component_by_name(pwm_hier_name), HierarchyWrapper)
        assert isinstance(top_hier_ipc._get_component_by_name(counters_hier_name), HierarchyWrapper)
        assert isinstance(top_hier_ipc._get_component_by_name(select_mod_name), IPWrapper)

    def test_top_hierarchy_connections(
        self,
        hier_top_ipconnect,
        top_hier_name,
        pwm_hier_name,
        counters_hier_name,
        select_mod_name,
        top_hierarchy_connections,
    ):
        """Check if all the defined connections are present in top_hierarchy"""
        top_hier_ipc = _get_inner_ipconnect(hier_top_ipconnect, top_hier_name)
        assert hasattr(top_hier_ipc, pwm_hier_name)
        assert hasattr(top_hier_ipc, counters_hier_name)
        assert hasattr(top_hier_ipc, select_mod_name)
        assert (
            len(getattr(top_hier_ipc, pwm_hier_name))
            + len(getattr(top_hier_ipc, counters_hier_name))
            + len(getattr(top_hier_ipc, select_mod_name))
            == top_hierarchy_connections
        )

    # Tests for pwm hierarchy:
    def test_pwm_hierarchy_ports(
        self, hier_top_ipconnect, top_hier_name, pwm_hier_name, pwm_hierarchy_ports
    ):
        """Check if pwm hierarchy (which wraps only pwm module) has all the defined ports"""
        pwm_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, pwm_hier_name
        )
        assert len(_get_ip_ports_by_dir(pwm_hier_ipc, DIR_IN)) == 2
        assert len(_get_ip_ports_by_dir(pwm_hier_ipc, DIR_OUT)) == 1
        assert sorted([port.name for port in pwm_hier_ipc.get_ports()]) == pwm_hierarchy_ports

    def test_pwm_hierarchy_components(
        self, hier_top_ipconnect, top_hier_name, pwm_hier_name, pwm_mod_name
    ):
        """Check if pwm hierarchy contains only the pwm module"""
        pwm_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, pwm_hier_name
        )
        assert len(pwm_hier_ipc._components) == 1
        assert isinstance(pwm_hier_ipc._get_component_by_name(pwm_mod_name), IPWrapper)

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

    # Test for down-counter module:
    def test_counter_down_module_ports(
        self,
        hier_top_ipconnect,
        top_hier_name,
        counters_hier_name,
        counter_down_mod_name,
        counter_down_module_ports,
    ):
        """Check counter_down module ports - check their directions, names and widths"""
        cnt_hier_ipc = _get_second_level_hier_by_name(
            hier_top_ipconnect, top_hier_name, counters_hier_name
        )
        cnt_ipw = cnt_hier_ipc._get_component_by_name(counter_down_mod_name)
        assert len(_get_ip_ports_by_dir(cnt_ipw, DIR_IN)) == 1
        assert len(_get_ip_ports_by_dir(cnt_ipw, DIR_OUT)) == 1
        assert (
            sorted([(port.name, len(port)) for port in cnt_ipw.get_ports()])
            == counter_down_module_ports
        )

    # Test for sig select module:
    def test_sig_select_module_ports(
        self, hier_top_ipconnect, top_hier_name, select_mod_name, select_module_ports
    ):
        """Check sig_select module ports - check their directions, names and widths"""
        top_hier_ipc = _get_inner_ipconnect(hier_top_ipconnect, top_hier_name)
        select_ipw = top_hier_ipc._get_component_by_name(select_mod_name)
        assert isinstance(select_ipw, IPWrapper)
        assert len(_get_ip_ports_by_dir(select_ipw, DIR_IN)) == 3
        assert len(_get_ip_ports_by_dir(select_ipw, DIR_OUT)) == 1
        assert (
            sorted([(port.name, len(port)) for port in select_ipw.get_ports()])
            == select_module_ports
        )
