 ## HDMI_OUT:0.DATA0_P
set_property PACKAGE_PIN W18 [get_ports HDMI_D0_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D0_P]
 ## HDMI_OUT:0.DATA0_N
set_property PACKAGE_PIN W19 [get_ports HDMI_D0_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D0_N]
 ## HDMI_OUT:0.DATA1_P
set_property PACKAGE_PIN R16 [get_ports HDMI_D1_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D1_P]
 ## HDMI_OUT:0.DATA1_N
set_property PACKAGE_PIN R17 [get_ports HDMI_D1_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D1_N]
 ## HDMI_OUT:0.DATA2_P
set_property PACKAGE_PIN P15 [get_ports HDMI_D2_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D2_P]
 ## HDMI_OUT:0.DATA2_N
set_property PACKAGE_PIN P16 [get_ports HDMI_D2_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_D2_N]
 ## HDMI_OUT:0.clk_p
set_property PACKAGE_PIN V17 [get_ports HDMI_CLK_P]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_CLK_P]
 ## HDMI_OUT:0.clk_N
set_property PACKAGE_PIN V18 [get_ports HDMI_CLK_N]
set_property IOSTANDARD TMDS_33 [get_ports HDMI_CLK_N]

# LED1
set_property PACKAGE_PIN N17 [get_ports debug0]
set_property IOSTANDARD LVCMOS33 [get_ports debug0]

# LED2
set_property PACKAGE_PIN P18 [get_ports debug1]
set_property IOSTANDARD LVCMOS33 [get_ports debug1]


#set_false_path -through [get_pins axi_dispctrl_v1_0_top/ip/Inst_vdma_to_vga/*_reg]

set_max_delay -datapath_only -from [get_pins cdc_flag_top/ip/A_reg_reg/C] -to [get_pins {cdc_flag_top/ip/B_reg_reg[0]/D}] 5.000
set_max_delay -datapath_only -from [get_pins axi_dispctrl_v1_0_top/ip/Inst_vdma_to_vga/running_reg_reg/C] -to [get_pins {axi_dispctrl_v1_0_top/ip/vga_running_sync_reg[0]/D}] 5.000
set_max_delay -datapath_only -from [get_pins axi_dispctrl_v1_0_top/ip/enable_reg_reg/C] -to [get_pins {axi_dispctrl_v1_0_top/ip/Inst_vdma_to_vga/vga_en_sync_reg[0]/D}] 5.000
