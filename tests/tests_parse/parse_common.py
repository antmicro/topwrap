# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re

from topwrap.hdl_parsers_utils import PortDefinition, PortDirection
from topwrap.interface_grouper import (
    IfacePortSpecification,
    InterfaceMatch,
    InterfaceMode,
    InterfaceSignalType,
)

AXI_AXIL_ADAPTER_S_AXI_IFACE = InterfaceMatch(
    signals={
        IfacePortSpecification(
            name="BVALID",
            regexp=re.compile("bvalid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_bvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="AWREADY",
            regexp=re.compile("awready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="WREADY",
            regexp=re.compile("wready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_wready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RID",
            regexp=re.compile("rid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_rid",
            upper_bound="(AXI_ID_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="ARREADY",
            regexp=re.compile("arready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="AWLEN",
            regexp=re.compile("awlen"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awlen", upper_bound="7", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWCACHE",
            regexp=re.compile("awcache"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awcache", upper_bound="3", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWADDR",
            regexp=re.compile("awaddr"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awaddr",
            upper_bound="(ADDR_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="RRESP",
            regexp=re.compile("rresp"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_rresp", upper_bound="1", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="AWBURST",
            regexp=re.compile("awburst"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awburst", upper_bound="1", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="RDATA",
            regexp=re.compile("rdata"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_rdata",
            upper_bound="(AXI_DATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="AWVALID",
            regexp=re.compile("awvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WLAST",
            regexp=re.compile("wlast"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_wlast", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWID",
            regexp=re.compile("awid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awid",
            upper_bound="(AXI_ID_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="ARLEN",
            regexp=re.compile("arlen"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arlen", upper_bound="7", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWLOCK",
            regexp=re.compile("awlock"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awlock", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WDATA",
            regexp=re.compile("wdata"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_wdata",
            upper_bound="(AXI_DATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="ARID",
            regexp=re.compile("arid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arid",
            upper_bound="(AXI_ID_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="ARVALID",
            regexp=re.compile("arvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="BID",
            regexp=re.compile("bid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_bid",
            upper_bound="(AXI_ID_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="AWPROT",
            regexp=re.compile("awprot"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awprot", upper_bound="2", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WSTRB",
            regexp=re.compile("wstrb"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_wstrb",
            upper_bound="(AXI_STRB_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="WVALID",
            regexp=re.compile("wvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_wvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWSIZE",
            regexp=re.compile("awsize"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_awsize", upper_bound="2", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="BREADY",
            regexp=re.compile("bready"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_bready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARADDR",
            regexp=re.compile("araddr"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_araddr",
            upper_bound="(ADDR_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="ARBURST",
            regexp=re.compile("arburst"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arburst", upper_bound="1", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARCACHE",
            regexp=re.compile("arcache"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arcache", upper_bound="3", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARSIZE",
            regexp=re.compile("arsize"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arsize", upper_bound="2", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARLOCK",
            regexp=re.compile("arlock"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arlock", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="BRESP",
            regexp=re.compile("bresp"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_bresp", upper_bound="1", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RREADY",
            regexp=re.compile("rready"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_rready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARPROT",
            regexp=re.compile("arprot"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_arprot", upper_bound="2", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="RLAST",
            regexp=re.compile("rlast"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_rlast", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RVALID",
            regexp=re.compile("rvalid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s_axi_rvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
    },
    bus_type="AXI3",
    name="s_axi",
    mode=InterfaceMode.SLAVE,
)

AXI_AXIL_ADAPTER_M_AXIL_IFACE = InterfaceMatch(
    signals={
        IfacePortSpecification(
            name="ARPROT",
            regexp=re.compile("arprot"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_arprot", upper_bound="2", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="WDATA",
            regexp=re.compile("wdata"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_wdata",
            upper_bound="(AXIL_DATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="AWPROT",
            regexp=re.compile("awprot"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_awprot", upper_bound="2", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="AWADDR",
            regexp=re.compile("awaddr"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_awaddr",
            upper_bound="(ADDR_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="AWREADY",
            regexp=re.compile("awready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_awready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWVALID",
            regexp=re.compile("awvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_awvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RREADY",
            regexp=re.compile("rready"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_rready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="BVALID",
            regexp=re.compile("bvalid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_bvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WVALID",
            regexp=re.compile("wvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_wvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="ARREADY",
            regexp=re.compile("arready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_arready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WSTRB",
            regexp=re.compile("wstrb"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_wstrb",
            upper_bound="(AXIL_STRB_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="BREADY",
            regexp=re.compile("bready"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_bready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="ARADDR",
            regexp=re.compile("araddr"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_araddr",
            upper_bound="(ADDR_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="WREADY",
            regexp=re.compile("wready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_wready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARVALID",
            regexp=re.compile("arvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_arvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="BRESP",
            regexp=re.compile("bresp"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_bresp", upper_bound="1", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="RRESP",
            regexp=re.compile("rresp"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_rresp", upper_bound="1", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="RDATA",
            regexp=re.compile("rdata"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_rdata",
            upper_bound="(AXIL_DATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="RVALID",
            regexp=re.compile("rvalid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="m_axil_rvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
    },
    bus_type="AXI4Lite",
    name="m_axil",
    mode=InterfaceMode.MASTER,
)

AXI_AXIL_ADAPTER_IFACES = [AXI_AXIL_ADAPTER_M_AXIL_IFACE, AXI_AXIL_ADAPTER_S_AXI_IFACE]

AXI_AXIL_ADAPTER_MASTER_PORTS = list(AXI_AXIL_ADAPTER_M_AXIL_IFACE.signals.values())
AXI_AXIL_ADAPTER_SLAVE_PORTS = list(AXI_AXIL_ADAPTER_S_AXI_IFACE.signals.values())

AXI_AXIL_ADAPTER_PORTS = (
    [
        PortDefinition("clk", "0", "0", PortDirection.IN),
        PortDefinition("rst", "0", "0", PortDirection.IN),
    ]
    + AXI_AXIL_ADAPTER_SLAVE_PORTS
    + AXI_AXIL_ADAPTER_MASTER_PORTS
)

AXI_DISPCTRL_S00_AXI_IFACE = InterfaceMatch(
    signals={
        IfacePortSpecification(
            name="AWADDR",
            regexp=re.compile("awaddr"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_awaddr",
            upper_bound="(C_S00_AXI_ADDR_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="ARPROT",
            regexp=re.compile("arprot"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_arprot", upper_bound="2", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WSTRB",
            regexp=re.compile("wstrb"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_wstrb",
            upper_bound="((C_S00_AXI_DATA_WIDTH/8)-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="AWPROT",
            regexp=re.compile("awprot"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_awprot", upper_bound="2", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="BREADY",
            regexp=re.compile("bready"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_bready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="WDATA",
            regexp=re.compile("wdata"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_wdata",
            upper_bound="(C_S00_AXI_DATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="BVALID",
            regexp=re.compile("bvalid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_bvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="WVALID",
            regexp=re.compile("wvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_wvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARREADY",
            regexp=re.compile("arready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_arready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="AWVALID",
            regexp=re.compile("awvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_awvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="AWREADY",
            regexp=re.compile("awready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_awready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RREADY",
            regexp=re.compile("rready"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_rready", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="ARADDR",
            regexp=re.compile("araddr"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_araddr",
            upper_bound="(C_S00_AXI_ADDR_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="WREADY",
            regexp=re.compile("wready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_wready", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="ARVALID",
            regexp=re.compile("arvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_arvalid", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="BRESP",
            regexp=re.compile("bresp"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_bresp", upper_bound="1", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RRESP",
            regexp=re.compile("rresp"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_rresp", upper_bound="1", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="RDATA",
            regexp=re.compile("rdata"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_rdata",
            upper_bound="(C_S00_AXI_DATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.OUT,
        ),
        IfacePortSpecification(
            name="RVALID",
            regexp=re.compile("rvalid"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="s00_axi_rvalid", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
    },
    bus_type="AXI4Lite",
    name="s00_axi",
    mode=InterfaceMode.SLAVE,
)

AXI_DISPCTRL_S_AXIS_IFACE = InterfaceMatch(
    signals={
        IfacePortSpecification(
            name="TDATA",
            regexp=re.compile("tdata"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="S_AXIS_TDATA",
            upper_bound="(C_S_AXIS_TDATA_WIDTH-1)",
            lower_bound="0",
            direction=PortDirection.IN,
        ),
        IfacePortSpecification(
            name="TVALID",
            regexp=re.compile("tvalid"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="S_AXIS_TVALID", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="TREADY",
            regexp=re.compile("tready"),
            direction=PortDirection.IN,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="S_AXIS_TREADY", upper_bound="0", lower_bound="0", direction=PortDirection.OUT
        ),
        IfacePortSpecification(
            name="TLAST",
            regexp=re.compile("tlast"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.REQUIRED,
        ): PortDefinition(
            name="S_AXIS_TLAST", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
        IfacePortSpecification(
            name="TUSER",
            regexp=re.compile("tuser"),
            direction=PortDirection.OUT,
            type=InterfaceSignalType.OPTIONAL,
        ): PortDefinition(
            name="S_AXIS_TUSER", upper_bound="0", lower_bound="0", direction=PortDirection.IN
        ),
    },
    bus_type="AXI4Stream",
    name="S_AXIS",
    mode=InterfaceMode.SLAVE,
)

AXI_DISPCTRL_IFACES = [AXI_DISPCTRL_S_AXIS_IFACE, AXI_DISPCTRL_S00_AXI_IFACE]

AXI_DISPCTRL_S_AXIS_PORTS = list(AXI_DISPCTRL_S_AXIS_IFACE.signals.values())
AXI_DISPCTRL_S00_AXI_PORTS = list(AXI_DISPCTRL_S00_AXI_IFACE.signals.values())

AXI_DISPCTRL_PORTS = (
    AXI_DISPCTRL_S_AXIS_PORTS
    + AXI_DISPCTRL_S00_AXI_PORTS
    + [
        PortDefinition("FSYNC_O", "0", "0", PortDirection.OUT),
        PortDefinition("HSYNC_O", "0", "0", PortDirection.OUT),
        PortDefinition("VSYNC_O", "0", "0", PortDirection.OUT),
        PortDefinition("DE_O", "0", "0", PortDirection.OUT),
        PortDefinition("DATA_O", "(C_S_AXIS_TDATA_WIDTH-1)", "0", PortDirection.OUT),
        PortDefinition("CTL_O", "3", "0", PortDirection.OUT),
        PortDefinition("VGUARD_O", "0", "0", PortDirection.OUT),
        PortDefinition("DGUARD_O", "0", "0", PortDirection.OUT),
        PortDefinition("DIEN_O", "0", "0", PortDirection.OUT),
        PortDefinition("DIH_O", "0", "0", PortDirection.OUT),
        PortDefinition("LOCKED_I", "0", "0", PortDirection.IN),
        PortDefinition("s00_axi_aclk", "0", "0", PortDirection.IN),
        PortDefinition("S_AXIS_ACLK", "0", "0", PortDirection.IN),
        PortDefinition("s00_axi_aresetn", "0", "0", PortDirection.IN),
    ]
)
