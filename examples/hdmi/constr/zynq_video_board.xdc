set_property PACKAGE_PIN B19 [get_ports HDMI_CLK_P]
set_property PACKAGE_PIN B20 [get_ports HDMI_CLK_N]
set_property PACKAGE_PIN F21 [get_ports HDMI_D0_P]
set_property PACKAGE_PIN F22 [get_ports HDMI_D0_N]
set_property PACKAGE_PIN H22 [get_ports HDMI_D1_P]
set_property PACKAGE_PIN G22 [get_ports HDMI_D1_N]
set_property PACKAGE_PIN E19 [get_ports HDMI_D2_P]
set_property PACKAGE_PIN E20 [get_ports HDMI_D2_N]

set_property IOSTANDARD TMDS_33 [get_ports HDMI_D0_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D0_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D1_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D1_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D2_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D2_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_CLK_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_CLK_P]

set_max_delay -datapath_only -from [get_pins cdc_flag_top/ip/A_reg_reg/C] -to [get_pins {cdc_flag_top/ip/B_reg_reg[0]/D}] 5.000
set_max_delay -datapath_only -from [get_pins axi_dispctrl_v1_0_top/ip/Inst_vdma_to_vga/running_reg_reg/C] -to [get_pins {axi_dispctrl_v1_0_top/ip/vga_running_sync_reg[0]/D}] 5.000
set_max_delay -datapath_only -from [get_pins axi_dispctrl_v1_0_top/ip/enable_reg_reg/C] -to [get_pins {axi_dispctrl_v1_0_top/ip/Inst_vdma_to_vga/vga_en_sync_reg[0]/D}] 5.000
