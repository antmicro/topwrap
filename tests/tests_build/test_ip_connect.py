# amaranth: UnusedElaboratable=no

# Copyright (C) 2021-2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
import pytest
from pathlib import Path
from fpga_topwrap.nm_helper import DIR_IN, DIR_OUT, DIR_INOUT
from fpga_topwrap.ipconnect import IPConnect
from fpga_topwrap.ipwrapper import IPWrapper


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
# IPWrapper and HierarchyWrapper structures
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
def dmatop_axism0_ports_names() -> list:
    return ['i_AXIS_m0_TREADY', 'o_AXIS_m0_TDATA', 'o_AXIS_m0_TLAST', 'o_AXIS_m0_TUSER', 'o_AXIS_m0_TVALID']

@pytest.fixture
def axi_dispctrl_axiss0_ports_names() -> list:
    return ['i_AXIS_s0_TDATA', 'i_AXIS_s0_TLAST', 'i_AXIS_s0_TUSER', 'i_AXIS_s0_TVALID', 'o_AXIS_s0_TREADY']

@pytest.fixture
def ext_axism0_ports_names() -> list:
    return ['ext_axis_TDATA', 'ext_axis_TLAST', 'ext_axis_TREADY', 'ext_axis_TUSER', 'ext_axis_TVALID']


class TestIPConnect:
    def test_add_component(self, dmatop_ipw, dmatop_name):
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        assert ipc._get_component_by_name(dmatop_name) == dmatop_ipw
        with pytest.raises(ValueError):
            ipc._get_component_by_name("non_existing_comp_name")


    def test_connect_ports(self, dmatop_ipw, dmatop_name, axi_dispctrl_ipw, axi_dispctrl_name):
        """Test connecting two IPs ports.
        """
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)

        dmatop_port_name = "io_sync_writerSync"
        axi_dispctrl_port_name = "HSYNC_O"
        combined_name = f"{dmatop_port_name}_{axi_dispctrl_port_name}"

        ipc.connect_ports(dmatop_port_name, dmatop_name, axi_dispctrl_port_name, axi_dispctrl_name)

        dmatop_port_full_name = "i_io_sync_writerSync"
        axi_dispctrl_port_full_name = "o_HSYNC_O"
        sig_dmatop = getattr(ipc, dmatop_name)[dmatop_port_full_name]
        sig_axi_dispctrl = getattr(ipc, axi_dispctrl_name)[axi_dispctrl_port_full_name]

        assert sig_dmatop.name == combined_name
        assert sig_axi_dispctrl.name == combined_name

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc.connect_ports(dmatop_port_name, dmatop_name, "non_existing_port_name", axi_dispctrl_name)
        with pytest.raises(ValueError):
            ipc.connect_ports(dmatop_port_name, "non_existing_comp_name", axi_dispctrl_port_name, axi_dispctrl_name)


    def test_connect_interfaces(self, dmatop_ipw, dmatop_name, axi_dispctrl_ipw, axi_dispctrl_name, dmatop_axism0_ports_names, axi_dispctrl_axiss0_ports_names):
        """Test connecting two IPs interfaces.
        """
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)

        dmatop_iface = "AXIS_m0"
        axi_dispctrl_iface = "AXIS_s0"

        ipc.connect_interfaces(dmatop_iface, dmatop_name, axi_dispctrl_iface, axi_dispctrl_name)

        sigs_dmatop = getattr(ipc, dmatop_name)
        sigs_axi_dispctrl = getattr(ipc, axi_dispctrl_name)

        assert sorted(list(sigs_dmatop.keys())) == dmatop_axism0_ports_names
        assert sorted(list(sigs_axi_dispctrl.keys())) == axi_dispctrl_axiss0_ports_names

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc.connect_interfaces(dmatop_iface, dmatop_name, "non_existing_iface_name", axi_dispctrl_name)
        with pytest.raises(ValueError):
            ipc.connect_interfaces(dmatop_iface, "non_existing_comp_name", axi_dispctrl_iface, axi_dispctrl_name)


    def test_set_port(self, dmatop_ipw, dmatop_name, axi_dispctrl_ipw, axi_dispctrl_name):
        """Test setting a port as external in the top module
        """
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)
        ipc.add_component(axi_dispctrl_name, axi_dispctrl_ipw)

        # Check simple creation of external reset port
        sig_dmatop_reset = "reset"
        sig_dmatop_reset_external = "ext_reset"
        ipc._set_port(dmatop_name, sig_dmatop_reset, sig_dmatop_reset_external, DIR_IN)
        assert len(ipc.get_ports()) == 1 and ipc.get_ports()[0].name == sig_dmatop_reset_external

        # Check creating 1 external input port which is connected to 2 different inputs
        sig_dmatop_clk, sig_axi_dispctrl_clk = "clock", "S_AXIS_ACLK"
        sig_clk_external = "ext_clk"
        ipc._set_port(dmatop_name, sig_dmatop_clk, sig_clk_external, DIR_IN)
        ipc._set_port(axi_dispctrl_name, sig_axi_dispctrl_clk, sig_clk_external, DIR_IN)
        assert len(ipc.get_ports()) == 2 and sig_clk_external in [sig.name for sig in ipc.get_ports()]
        assert sig_clk_external in [sig.name for sig in getattr(ipc, dmatop_name).values()]
        assert sig_clk_external in [sig.name for sig in getattr(ipc, axi_dispctrl_name).values()]

        # Check whether connecting 2 output ports to a single external output results in ValueError
        with pytest.raises(ValueError):
            sig_dmatop_out, sig_axi_dispctrl_out = "io_irq_readerDone", "FSYNC_O"
            sig_out_external = "ext_sig"
            ipc._set_port(dmatop_name, sig_dmatop_out, sig_out_external, DIR_OUT)
            ipc._set_port(axi_dispctrl_name, sig_axi_dispctrl_out, sig_out_external, DIR_OUT)

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc._set_port(dmatop_name, "non_existing_port_name", "sig_ext", DIR_IN)


    def test_set_interface(self, dmatop_ipw, dmatop_name, ext_axism0_ports_names):
        """Test setting an interface as external in the top module
        """
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)

        dmatop_iface = "AXIS_m0"
        ext_iface_name = "ext_axis"
        ipc._set_interface(dmatop_name, dmatop_iface, ext_iface_name)
        assert sorted([sig.name for sig in ipc.get_ports()]) == ext_axism0_ports_names

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc._set_interface(dmatop_name, "non_existing_iface_name", ext_iface_name)
        with pytest.raises(ValueError):
            ipc._set_interface("non_existing_comp_name", dmatop_iface, ext_iface_name)

    def test_set_constant(self, dmatop_ipw, dmatop_name):
        """Test setting a constant value on a port of a module
        """
        ipc = IPConnect()
        ipc.add_component(dmatop_name, dmatop_ipw)

        sig_dmatop_reset, full_sig_dmatop_reset = "reset", "i_reset"
        ipc.set_constant(dmatop_name, sig_dmatop_reset, 0)
        assert getattr(ipc, dmatop_name)[full_sig_dmatop_reset].value == 0

        # Check function behavior on invalid data
        with pytest.raises(ValueError):
            ipc.set_constant(dmatop_name, "non_existing_port_name", 0)
        with pytest.raises(ValueError):
            ipc.set_constant("non_existing_comp_name", "port", 0)
