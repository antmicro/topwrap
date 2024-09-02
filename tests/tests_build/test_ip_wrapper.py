# amaranth: UnusedElaboratable=no

# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from topwrap.ipwrapper import IPWrapper


# -----------------------------------------
# IP core names and description files paths
# -----------------------------------------
@pytest.fixture
def axi_dispctrl_name() -> str:
    return "axi_dispctrl_v1_0"


@pytest.fixture
def axi_dispctrl_yaml() -> Path:
    return Path("axi_dispctrl_v1_0.yaml")


@pytest.fixture
def axi_dispctrl_path(axi_dispctrl_yaml) -> Path:
    return Path("tests/data/data_build") / axi_dispctrl_yaml


# -----------------
# IPWrapper objects
# -----------------
@pytest.fixture
def axi_dispctrl_ipw(axi_dispctrl_path, axi_dispctrl_yaml) -> IPWrapper:
    return IPWrapper(axi_dispctrl_path, axi_dispctrl_name, axi_dispctrl_name, {})


@pytest.fixture
def axi_dispctrl_ipw_overriden(axi_dispctrl_name, axi_dispctrl_path) -> IPWrapper:
    return IPWrapper(
        axi_dispctrl_path,
        axi_dispctrl_name,
        axi_dispctrl_name,
        {"C_S_AXIS_TDATA_WIDTH": 64, "C_S00_AXI_DATA_WIDTH": 64},
    )


@pytest.fixture
def axi_dispctrl_ipw_custom_params(axi_dispctrl_name, axi_dispctrl_path) -> IPWrapper:
    return IPWrapper(
        axi_dispctrl_path,
        axi_dispctrl_name,
        axi_dispctrl_name,
        {"EX_WIDTH": 8, "EVAL_WIDTH": "EX_WIDTH/2", "EX_STRING": '"STRING"'},
    )


# ----------------------------------------------------------------------------
# Names of ports that should be created while initializing `IPWrapper` objects
# ----------------------------------------------------------------------------
@pytest.fixture
def axi_dispctrl_port_names_widths() -> list:
    return [
        ("S_AXIS_ACLK", 1),
        ("LOCKED_I", 1),
        ("s00_axi_aclk", 1),
        ("s00_axi_aresetn", 1),
        ("FSYNC_O", 1),
        ("HSYNC_O", 1),
        ("VSYNC_O", 1),
        ("DE_O", 1),
        ("DATA_O", 32),
        ("CTL_O", 4),
        ("VGUARD_O", 1),
        ("DGUARD_O", 1),
        ("DIEN_O", 1),
        ("DIH_O", 1),
        ("AXI_s0_AWADDR", 7),
        ("AXI_s0_AWPROT", 3),
        ("AXI_s0_AWVALID", 1),
        ("AXI_s0_WDATA", 32),
        ("AXI_s0_WSTRB", 4),
        ("AXI_s0_WVALID", 1),
        ("AXI_s0_BREADY", 1),
        ("AXI_s0_ARADDR", 7),
        ("AXI_s0_ARPROT", 3),
        ("AXI_s0_ARVALID", 1),
        ("AXI_s0_RREADY", 1),
        ("AXI_s0_AWREADY", 1),
        ("AXI_s0_WREADY", 1),
        ("AXI_s0_BRESP", 2),
        ("AXI_s0_BVALID", 1),
        ("AXI_s0_ARREADY", 1),
        ("AXI_s0_RDATA", 32),
        ("AXI_s0_RRESP", 2),
        ("AXI_s0_RVALID", 1),
        ("AXIS_s0_TVALID", 1),
        ("AXIS_s0_TDATA", 32),
        ("AXIS_s0_TLAST", 1),
        ("AXIS_s0_TUSER", 1),
        ("AXIS_s0_TREADY", 1),
    ]


@pytest.fixture
def axi_dispctrl_overriden_port_names_widths() -> list:
    return [
        ("S_AXIS_ACLK", 1),
        ("LOCKED_I", 1),
        ("s00_axi_aclk", 1),
        ("s00_axi_aresetn", 1),
        ("FSYNC_O", 1),
        ("HSYNC_O", 1),
        ("VSYNC_O", 1),
        ("DE_O", 1),
        ("DATA_O", 64),
        ("CTL_O", 4),
        ("VGUARD_O", 1),
        ("DGUARD_O", 1),
        ("DIEN_O", 1),
        ("DIH_O", 1),
        ("AXI_s0_AWADDR", 7),
        ("AXI_s0_AWPROT", 3),
        ("AXI_s0_AWVALID", 1),
        ("AXI_s0_WDATA", 64),
        ("AXI_s0_WSTRB", 8),
        ("AXI_s0_WVALID", 1),
        ("AXI_s0_BREADY", 1),
        ("AXI_s0_ARADDR", 7),
        ("AXI_s0_ARPROT", 3),
        ("AXI_s0_ARVALID", 1),
        ("AXI_s0_RREADY", 1),
        ("AXI_s0_AWREADY", 1),
        ("AXI_s0_WREADY", 1),
        ("AXI_s0_BRESP", 2),
        ("AXI_s0_BVALID", 1),
        ("AXI_s0_ARREADY", 1),
        ("AXI_s0_RDATA", 64),
        ("AXI_s0_RRESP", 2),
        ("AXI_s0_RVALID", 1),
        ("AXIS_s0_TVALID", 1),
        ("AXIS_s0_TDATA", 64),
        ("AXIS_s0_TLAST", 1),
        ("AXIS_s0_TUSER", 1),
        ("AXIS_s0_TREADY", 1),
    ]


@pytest.fixture
def axi_dispctrl_interfaces() -> list:
    """Return a list of interfaces and number of ports belonging to them"""
    return [("AXI_s0", 19), ("AXIS_s0", 5)]


class TestIPWrapper:
    def test_ports_no_override(self, axi_dispctrl_ipw, axi_dispctrl_port_names_widths):
        """Check whether all the ports of `IPWrapper` object have been created"""
        for port_name, port_width in axi_dispctrl_port_names_widths:
            ipw_port = axi_dispctrl_ipw.get_port_by_name(port_name)
            assert len(ipw_port) == port_width

    def test_ports_override(
        self, axi_dispctrl_ipw_overriden, axi_dispctrl_overriden_port_names_widths
    ):
        """Check whether all the ports of `IPWrapper` object have been created, but this time
        taking into account the overridden parameters values.
        """
        for port_name, port_width in axi_dispctrl_overriden_port_names_widths:
            ipw_port = axi_dispctrl_ipw_overriden.get_port_by_name(port_name)
            assert len(ipw_port) == port_width

    def test_get_port_by_name_invalid_name(self, axi_dispctrl_ipw):
        with pytest.raises(ValueError):
            axi_dispctrl_ipw.get_port_by_name("non_existing_port_name")

    def test_get_port_by_interface(self, axi_dispctrl_ipw, axi_dispctrl_interfaces):
        for iface_name, num_ports in axi_dispctrl_interfaces:
            assert len(axi_dispctrl_ipw.get_ports_of_interface(iface_name)) == num_ports

        with pytest.raises(ValueError):
            axi_dispctrl_ipw.get_ports_of_interface("non_existing_iface_name")

    def test_params_evalutaion(self, axi_dispctrl_ipw_custom_params):
        assert axi_dispctrl_ipw_custom_params._parameters == {
            "p_EX_WIDTH": 8,
            "p_EVAL_WIDTH": 4.0,
            "p_EX_STRING": "STRING",
        }
