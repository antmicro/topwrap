# amaranth: UnusedElaboratable=no

# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from typing import Dict

import pytest
from amaranth.hdl import ast

from topwrap.amaranth_helpers import DIR_IN, DIR_INOUT, DIR_OUT
from topwrap.ipconnect import IPConnect
from topwrap.ipwrapper import IPWrapper


# -------------------------------------
# IP core names and description files paths
# -------------------------------------
@pytest.fixture
def dmatop_name() -> str:
    return "DMATop"


@pytest.fixture
def axi_dispctrl_name() -> str:
    return "axi_dispctrl_v1_0"


@pytest.fixture
def dmatop_yaml() -> Path:
    return Path("tests/data/data_build/DMATop.yaml")


@pytest.fixture
def axi_dispctrl_yaml() -> Path:
    return Path("tests/data/data_build/axi_dispctrl_v1_0.yaml")


# -------------------------------------
# IPWrapper and hierarchy IPConnect structures
# -------------------------------------
@pytest.fixture
def dmatop_ipw(dmatop_yaml, dmatop_name) -> IPWrapper:
    return IPWrapper(dmatop_yaml, dmatop_name, dmatop_name)


@pytest.fixture
def axi_dispctrl_ipw(axi_dispctrl_yaml, axi_dispctrl_name) -> IPWrapper:
    return IPWrapper(axi_dispctrl_yaml, axi_dispctrl_name, axi_dispctrl_name)


# -------------------------------------
# Fixtures for specific tests
# -------------------------------------
@pytest.fixture
def dmatop_to_axi_dispctrl_ports_connections() -> Dict[str, str]:
    return {
        "AXIS_m0_TREADY": "AXIS_s0_TREADY",
        "AXIS_s0_TVALID": "AXIS_m0_TVALID",
        "AXIS_s0_TDATA": "AXIS_m0_TDATA",
        "AXIS_s0_TLAST": "AXIS_m0_TLAST",
        "AXIS_s0_TUSER": "AXIS_m0_TUSER",
    }


@pytest.fixture
def ext_to_axism0_ports_connections() -> list:
    return {
        "AXIS_m0_TREADY": "ext_axis_TREADY",
        "ext_axis_TDATA": "AXIS_m0_TDATA",
        "ext_axis_TLAST": "AXIS_m0_TLAST",
        "ext_axis_TUSER": "AXIS_m0_TUSER",
        "ext_axis_TVALID": "AXIS_m0_TVALID",
    }


class TestIPConnect:
    def test_add_component(self, dmatop_ipw, dmatop_name):
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        assert ipc._get_component_by_name(dmatop_name) == dmatop_ipw
        with pytest.raises(ValueError):
            ipc._get_component_by_name("non_existing_comp_name")

    def test_connect_ports(self, dmatop_ipw, dmatop_name, axi_dispctrl_ipw, axi_dispctrl_name):
        """Test connecting two IPs ports."""
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)

        dmatop_port_name = "io_sync_writerSync"
        axi_dispctrl_port_name = "HSYNC_O"

        ipc.connect_ports(dmatop_port_name, dmatop_name, axi_dispctrl_port_name, axi_dispctrl_name)

        sig_dmatop = ipc._get_component_by_name(dmatop_name).get_port_by_name(dmatop_port_name)
        sig_axi_dispctrl = ipc._get_component_by_name(axi_dispctrl_name).get_port_by_name(
            axi_dispctrl_port_name
        )
        [conn] = ipc._connections

        assert isinstance(conn, ast.Assign)
        assert conn.lhs is sig_dmatop
        assert conn.rhs is sig_axi_dispctrl

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc.connect_ports(
                dmatop_port_name, dmatop_name, "non_existing_port_name", axi_dispctrl_name
            )
        with pytest.raises(ValueError):
            ipc.connect_ports(
                dmatop_port_name,
                "non_existing_comp_name",
                axi_dispctrl_port_name,
                axi_dispctrl_name,
            )

        # Check that connecting two internal inout ports raises a ValueError
        with pytest.raises(ValueError):
            ipc.connect_ports("some_inout1", axi_dispctrl_name, "some_inout2", axi_dispctrl_name)

    def test_connect_interfaces(
        self,
        dmatop_ipw,
        dmatop_name,
        axi_dispctrl_ipw,
        axi_dispctrl_name,
        dmatop_to_axi_dispctrl_ports_connections,
    ):
        """Test connecting two IPs interfaces."""
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)

        dmatop_iface = "AXIS_m0"
        axi_dispctrl_iface = "AXIS_s0"

        ipc.connect_interfaces(dmatop_iface, dmatop_name, axi_dispctrl_iface, axi_dispctrl_name)

        sigs_dmatop = dmatop_ipw.get_ports_of_interface(dmatop_iface)
        sigs_axi_dispctrl = axi_dispctrl_ipw.get_ports_of_interface(axi_dispctrl_iface)

        name_sig = {sig.name: sig for sig in [*sigs_dmatop, *sigs_axi_dispctrl]}

        for conn in ipc._connections:
            assert isinstance(conn, ast.Assign)
            lhs = conn.lhs
            rhs = conn.rhs

            assert lhs.name in dmatop_to_axi_dispctrl_ports_connections
            assert rhs.name == dmatop_to_axi_dispctrl_ports_connections[lhs.name]
            assert name_sig[lhs.name] is lhs
            assert name_sig[rhs.name] is rhs

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc.connect_interfaces(
                dmatop_iface, dmatop_name, "non_existing_iface_name", axi_dispctrl_name
            )
        with pytest.raises(ValueError):
            ipc.connect_interfaces(
                dmatop_iface, "non_existing_comp_name", axi_dispctrl_iface, axi_dispctrl_name
            )

    def test_set_port(self, dmatop_ipw, dmatop_name, axi_dispctrl_ipw, axi_dispctrl_name):
        """Test setting a port as external in the top module"""
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)

        # Check simple creation of external reset port
        sig_dmatop_reset = "reset"
        sig_dmatop_reset_external = "ext_reset"
        ipc._set_port(dmatop_name, sig_dmatop_reset, sig_dmatop_reset_external)

        [conn] = ipc._connections
        assert isinstance(conn, ast.Assign)
        assert len(ipc.get_ports()) == 1
        assert conn.lhs is dmatop_ipw.get_port_by_name(sig_dmatop_reset)
        assert conn.rhs is ipc.get_port_by_name(sig_dmatop_reset_external)

        # Check creating 1 external input port which is connected to 2 different inputs
        sig_dmatop_clk, sig_axi_dispctrl_clk = "clock", "S_AXIS_ACLK"
        sig_clk_external = "ext_clk"
        ipc._set_port(dmatop_name, sig_dmatop_clk, sig_clk_external)
        ipc._set_port(axi_dispctrl_name, sig_axi_dispctrl_clk, sig_clk_external)
        for ipw, input_sig in (
            (dmatop_ipw, sig_dmatop_clk),
            (axi_dispctrl_ipw, sig_axi_dispctrl_clk),
        ):
            [conn] = [conn for conn in ipc._connections if conn.lhs.name == input_sig]
            assert isinstance(conn, ast.Assign)
            assert len(ipc.get_ports()) == 2
            assert conn.lhs is ipw.get_port_by_name(input_sig)
            assert conn.rhs is ipc.get_port_by_name(sig_clk_external)

        # Check whether connecting 2 output ports to a single external output results in ValueError
        with pytest.raises(ValueError):
            sig_dmatop_out, sig_axi_dispctrl_out = "io_irq_readerDone", "FSYNC_O"
            sig_out_external = "ext_sig"
            ipc._set_port(dmatop_name, sig_dmatop_out, sig_out_external)
            ipc._set_port(axi_dispctrl_name, sig_axi_dispctrl_out, sig_out_external)

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc._set_port(dmatop_name, "non_existing_port_name", "sig_ext")

        # Check that connecting internal inout port to external inout port raises a ValueError
        with pytest.raises(ValueError):
            ipc._set_port(axi_dispctrl_name, "some_inout1", "external_inout")

    def test_set_interface(self, dmatop_ipw, dmatop_name, ext_to_axism0_ports_connections):
        """Test setting an interface as external in the top module"""
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)

        dmatop_iface = "AXIS_m0"
        ext_iface_name = "ext_axis"
        ipc._set_interface(dmatop_name, dmatop_iface, ext_iface_name)

        sigs_dmatop = dmatop_ipw.get_ports_of_interface(dmatop_iface)
        sigs_ipc = ipc.get_ports_of_interface(ext_iface_name)

        name_sig = {sig.name: sig for sig in [*sigs_dmatop, *sigs_ipc]}

        for conn in ipc._connections:
            assert isinstance(conn, ast.Assign)
            lhs = conn.lhs
            rhs = conn.rhs

            assert lhs.name in ext_to_axism0_ports_connections
            assert rhs.name == ext_to_axism0_ports_connections[lhs.name]
            assert name_sig[lhs.name] is lhs
            assert name_sig[rhs.name] is rhs

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc._set_interface(dmatop_name, "non_existing_iface_name", ext_iface_name)
        with pytest.raises(ValueError):
            ipc._set_interface("non_existing_comp_name", dmatop_iface, ext_iface_name)

    def test_set_constant(self, dmatop_ipw, dmatop_name):
        """Test setting a constant value on a port of a module"""
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)

        sig_dmatop_reset = "reset"
        ipc.set_constant(dmatop_name, sig_dmatop_reset, 0)
        [conn] = [conn for conn in ipc._connections if conn.lhs.name == sig_dmatop_reset]
        assert isinstance(conn, ast.Assign)
        assert conn.lhs is dmatop_ipw.get_port_by_name(sig_dmatop_reset)
        assert conn.rhs.value == 0

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc.set_constant(dmatop_name, "non_existing_port_name", 0)
        with pytest.raises(ValueError):
            ipc.set_constant("non_existing_comp_name", "port", 0)

    def test_validate_inout_connections(self, axi_dispctrl_name, axi_dispctrl_ipw):
        """Test validating that the user put all inout ports in the
        external.ports.inout section of YAML design file"""
        ipc = IPConnect("top")
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)
        conn1 = [axi_dispctrl_name, "some_inout1"]
        conn2 = [axi_dispctrl_name, "some_inout2"]

        # Negative case: user didn't put all inout ports in the external.ports.inout section
        with pytest.raises(ValueError):
            ipc.validate_inout_connections([conn1])
        # Positive case: user did put all inout ports in the external.ports.inout.section
        ipc.validate_inout_connections([conn1, conn2])
