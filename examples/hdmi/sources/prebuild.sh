# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
echo "Prebuild script started"
sed -i '8icreate_ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 -module_name proc_sys_reset_0' project_1_0.tcl
sed -i '8icreate_ip -vlnv xilinx.com:ip:axi_protocol_converter:2.1 -module_name axi_protocol_converter' project_1_0.tcl
sed -i '8icreate_ip -vlnv xilinx.com:ip:axis_dwidth_converter:1.1 -module_name dwidth_converter' project_1_0.tcl
sed -i 's/launch_runs synth_1/launch_runs synth_1 -jobs 16/g' project_1_0_synth.tcl
sed -i '14iset_property -dict [list CONFIG.SI_PROTOCOL {AXI4} CONFIG.MI_PROTOCOL {AXI3} CONFIG.DATA_WIDTH {64} CONFIG.TRANSLATION_MODE {2} CONFIG.ID_WIDTH {4}] [get_ips axi_protocol_converter]' project_1_0.tcl
sed -i 's/source_mgmt_mode None/source_mgmt_mode All/g' project_1_0.tcl
sed -i '15iset_property -dict [list CONFIG.S_TDATA_NUM_BYTES {8} CONFIG.M_TDATA_NUM_BYTES {4}] [get_ips dwidth_converter]' project_1_0.tcl
