library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library UNISIM;
use UNISIM.VCOMPONENTS.ALL;

entity axi_dispctrl_v1_0 is
	generic (
		-- Users to add parameters here
		-- Parameters of Axis slave interface S_AXIS
		C_S_AXIS_TDATA_WIDTH : integer := 32;
		-- User parameters ends
		-- Do not modify the parameters beyond this line
		-- Parameters of Axi Slave Bus Interface S00_AXI
		C_S00_AXI_DATA_WIDTH : integer := 32;
		C_S00_AXI_ADDR_WIDTH : integer := 7
	);
	port (
		-- Users to add ports here
		S_AXIS_ACLK : in std_logic; -- this should be connected to pxl_clk
		S_AXIS_TDATA : in std_logic_vector (C_S_AXIS_TDATA_WIDTH-1 downto 0);
		S_AXIS_TVALID : in std_logic;
		S_AXIS_TLAST : in std_logic;
		S_AXIS_TUSER : in std_logic_vector(0 downto 0);
		S_AXIS_TREADY : out std_logic;
		FSYNC_O : out std_logic;
		HSYNC_O : out std_logic;
		VSYNC_O : out std_logic;
		DE_O : out std_logic;
		DATA_O : out std_logic_vector(C_S_AXIS_TDATA_WIDTH-1 downto 0);
		CTL_O : out std_logic_vector(3 downto 0);
		VGUARD_O : out std_logic; -- Send video guard band
		DGUARD_O : out std_logic;
		DIEN_O : out std_logic;
		DIH_O : out std_logic;
		LOCKED_I : in std_logic;
		-- User ports ends
		-- Do not modify the ports beyond this line
		-- Ports of Axi Slave Bus Interface S00_AXI
		s00_axi_aclk : in std_logic;
		s00_axi_aresetn : in std_logic;
		s00_axi_awaddr : in std_logic_vector(C_S00_AXI_ADDR_WIDTH-1 downto 0);
		s00_axi_awprot : in std_logic_vector(2 downto 0);
		s00_axi_awvalid : in std_logic;
		s00_axi_awready : out std_logic;
		s00_axi_wdata : in std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
		s00_axi_wstrb : in std_logic_vector((C_S00_AXI_DATA_WIDTH/8)-1 downto 0);
		s00_axi_wvalid : in std_logic;
		s00_axi_wready : out std_logic;
		s00_axi_bresp : out std_logic_vector(1 downto 0);
		s00_axi_bvalid : out std_logic;
		s00_axi_bready : in std_logic;
		s00_axi_araddr : in std_logic_vector(C_S00_AXI_ADDR_WIDTH-1 downto 0);
		s00_axi_arprot : in std_logic_vector(2 downto 0);
		s00_axi_arvalid : in std_logic;
		s00_axi_arready : out std_logic;
		s00_axi_rdata : out std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
		s00_axi_rresp : out std_logic_vector(1 downto 0);
		s00_axi_rvalid : out std_logic;
		s00_axi_rready : in std_logic
	);
end axi_dispctrl_v1_0;

architecture arch_imp of axi_dispctrl_v1_0 is

	-- component declaration
	component axi_dispctrl_v1_0_S00_AXI is
	generic (
		C_S_AXI_DATA_WIDTH : integer := 32;
		C_S_AXI_ADDR_WIDTH : integer := 6
	);
	port (
		CTRL_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		STAT_REG : in std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		FRAME_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		HPARAM1_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		HPARAM2_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		VPARAM1_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		VPARAM2_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK0_O_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK1_O_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK_FB_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK_FRAC_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK_DIV_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK_LOCK_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		CLK_FLTR_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		PREAM_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		VGUARD_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		HDATAEN_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		VDATAEN_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		FSYNC_REG : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		S_AXI_ACLK : in std_logic;
		S_AXI_ARESETN : in std_logic;
		S_AXI_AWADDR : in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
		S_AXI_AWPROT : in std_logic_vector(2 downto 0);
		S_AXI_AWVALID : in std_logic;
		S_AXI_AWREADY : out std_logic;
		S_AXI_WDATA : in std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		S_AXI_WSTRB : in std_logic_vector((C_S_AXI_DATA_WIDTH/8)-1 downto 0);
		S_AXI_WVALID : in std_logic;
		S_AXI_WREADY : out std_logic;
		S_AXI_BRESP : out std_logic_vector(1 downto 0);
		S_AXI_BVALID : out std_logic;
		S_AXI_BREADY : in std_logic;
		S_AXI_ARADDR : in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
		S_AXI_ARPROT : in std_logic_vector(2 downto 0);
		S_AXI_ARVALID : in std_logic;
		S_AXI_ARREADY : out std_logic;
		S_AXI_RDATA : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		S_AXI_RRESP : out std_logic_vector(1 downto 0);
		S_AXI_RVALID : out std_logic;
		S_AXI_RREADY : in std_logic
	);
	end component axi_dispctrl_v1_0_S00_AXI;

	COMPONENT vdma_to_vga
	GENERIC(
		C_S_AXIS_TDATA_WIDTH : integer
	);
	PORT(
		LOCKED_I: IN std_logic;
		ENABLE_I : IN std_logic;
		S_AXIS_ACLK : in STD_LOGIC;
		S_AXIS_TDATA : in STD_LOGIC_VECTOR (C_S_AXIS_TDATA_WIDTH-1 downto 0);
		S_AXIS_TVALID : in STD_LOGIC;
		S_AXIS_TLAST : in std_logic;
		S_AXIS_TREADY : out STD_LOGIC;
		USR_HPS_I : IN std_logic_vector(11 downto 0);
		USR_HPE_I : IN std_logic_vector(11 downto 0);
		USR_HPOL_I : IN std_logic;
		USR_HPREAMS_I : IN std_logic_vector(11 downto 0);
		USR_HPREAME_I : IN std_logic_vector(11 downto 0);
		USR_VGUARDS_I : IN std_logic_vector(11 downto 0);
		USR_VGUARDE_I : IN std_logic_vector(11 downto 0);
		USR_HDATAENS_I : IN std_logic_vector(11 downto 0);
		USR_HDATAENE_I : IN std_logic_vector(11 downto 0);
		USR_VDATAENS_I : IN std_logic_vector(11 downto 0);
		USR_VDATAENE_I : IN std_logic_vector(11 downto 0);
		USR_DATAENPOL_I : IN std_logic;
		USR_HMAX_I : IN std_logic_vector(11 downto 0);
		USR_VPS_I : IN std_logic_vector(11 downto 0);
		USR_VPE_I : IN std_logic_vector(11 downto 0);
		USR_VPOL_I : IN std_logic;
		USR_VMAX_I : IN std_logic_vector(11 downto 0);
		USR_FSYNC_I : IN std_logic_vector(11 downto 0);
		RUNNING_O : OUT std_logic;
		FSYNC_O : OUT std_logic;
		HSYNC_O : OUT std_logic;
		VSYNC_O : OUT std_logic;
		DE_O : out STD_LOGIC;
		DATA_O : out STD_LOGIC_VECTOR (C_S_AXIS_TDATA_WIDTH-1 downto 0);
		CTL_O : out STD_LOGIC_VECTOR (3 downto 0);
		VGUARD_O : out STD_LOGIC;
		DGUARD_O : out STD_LOGIC;
		DIEN_O : out STD_LOGIC;
		DIH_O : out STD_LOGIC;
		DEBUG_O : out std_logic_vector(31 downto 0));
	END COMPONENT;

	-- signals
	signal ctrl_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal stat_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal frame_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal hparam1_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal hparam2_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal vparam1_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal vparam2_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk0_o_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk1_o_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk_fb_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk_frac_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk_div_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk_lock_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal clk_fltr_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal pream_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal vguard_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal hdataen_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal vdataen_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);
	signal fsync_reg : std_logic_vector(C_S00_AXI_DATA_WIDTH-1 downto 0);

	type CLK_STATE_TYPE is (RESET, WAIT_LOCKED, WAIT_EN, WAIT_SRDY, WAIT_RUN, ENABLED, WAIT_FRAME_DONE);

	signal locked : std_logic;
	signal srdy : std_logic := '1';

	signal enable_reg : std_logic := '0';
	signal sen_reg : std_logic := '0';

	signal vga_running : std_logic;

	attribute ASYNC_REG : string;
	signal vga_running_sync : std_logic_vector(2 downto 0) := (others => '0');
	attribute ASYNC_REG of vga_running_sync: signal is "TRUE";

	signal clk_state : CLK_STATE_TYPE := RESET;
	signal RST : std_logic;
	signal S1_CLKOUT0 : std_logic_vector(35 downto 0);
	signal S1_CLKOUT1 : std_logic_vector(35 downto 0);
	signal S1_CLKFBOUT : std_logic_vector(35 downto 0);
	signal S1_LOCK : std_logic_vector(39 downto 0);

begin

-- Instantiation of Axi Bus Interface S00_AXI
axi_dispctrl_v1_0_S00_AXI_inst : axi_dispctrl_v1_0_S00_AXI
	generic map (
		C_S_AXI_DATA_WIDTH => C_S00_AXI_DATA_WIDTH,
		C_S_AXI_ADDR_WIDTH => C_S00_AXI_ADDR_WIDTH
	)
	port map (
		CTRL_REG => ctrl_reg,
		STAT_REG => stat_reg,
		FRAME_REG => frame_reg,
		HPARAM1_REG => hparam1_reg,
		HPARAM2_REG => hparam2_reg,
		VPARAM1_REG => vparam1_reg,
		VPARAM2_REG => vparam2_reg,
		CLK0_O_REG => clk0_o_reg,
		CLK1_O_REG => clk1_o_reg,
		CLK_FB_REG => clk_fb_reg,
		CLK_FRAC_REG => clk_frac_reg,
		CLK_DIV_REG => clk_div_reg,
		CLK_LOCK_REG => clk_lock_reg,
		CLK_FLTR_REG => clk_fltr_reg,
		PREAM_REG => pream_reg,
		VGUARD_REG => vguard_reg,
		HDATAEN_REG => hdataen_reg,
		VDATAEN_REG => vdataen_reg,
		FSYNC_REG => fsync_reg,

		S_AXI_ACLK => s00_axi_aclk,
		S_AXI_ARESETN => s00_axi_aresetn,
		S_AXI_AWADDR => s00_axi_awaddr,
		S_AXI_AWPROT => s00_axi_awprot,
		S_AXI_AWVALID => s00_axi_awvalid,
		S_AXI_AWREADY => s00_axi_awready,
		S_AXI_WDATA => s00_axi_wdata,
		S_AXI_WSTRB => s00_axi_wstrb,
		S_AXI_WVALID => s00_axi_wvalid,
		S_AXI_WREADY => s00_axi_wready,
		S_AXI_BRESP => s00_axi_bresp,
		S_AXI_BVALID => s00_axi_bvalid,
		S_AXI_BREADY => s00_axi_bready,
		S_AXI_ARADDR => s00_axi_araddr,
		S_AXI_ARPROT => s00_axi_arprot,
		S_AXI_ARVALID => s00_axi_arvalid,
		S_AXI_ARREADY => s00_axi_arready,
		S_AXI_RDATA => s00_axi_rdata,
		S_AXI_RRESP => s00_axi_rresp,
		S_AXI_RVALID => s00_axi_rvalid,
		S_AXI_RREADY => s00_axi_rready
	);

	-- Add user logic here
	rst <= not(s00_axi_aresetn);
	S1_CLKOUT0 <= CLK_FRAC_REG(3 downto 0) & CLK0_O_REG;
	S1_CLKOUT1 <= CLK_FRAC_REG(3 downto 0) & CLK1_O_REG;
	S1_CLKFBOUT <= CLK_FRAC_REG(19 downto 16) & CLK_FB_REG;
	S1_LOCK <= CLK_FLTR_REG(7 downto 0) & CLK_LOCK_REG;

	locked <= LOCKED_I;

	process (s00_axi_aclk)
		begin
		if (rising_edge(s00_axi_aclk)) then
			if (s00_axi_aresetn = '0') then
				clk_state <= RESET;
			else
				case clk_state is
					when RESET =>
						clk_state <= WAIT_LOCKED;
					when WAIT_LOCKED =>  --This state ensures that the initial SRDY pulse doesnt interfere with the WAIT_SRDY state
						if (locked = '1') then
							clk_state <= WAIT_EN;
						end if;
					when WAIT_EN =>
						if (CTRL_REG(0) = '1') then
							clk_state <= WAIT_SRDY;
						end if;
					when WAIT_SRDY =>
						if (srdy = '1') then
							clk_state <= WAIT_RUN;
						end if;
					when WAIT_RUN =>
						if (STAT_REG(0) = '1') then
							clk_state <= ENABLED;
						end if;
					when ENABLED =>
						if (CTRL_REG(0) = '0') then
							clk_state <= WAIT_FRAME_DONE;
						end if;
					when WAIT_FRAME_DONE =>
						if (STAT_REG(0) = '0') then
							clk_state <= WAIT_EN;
						end if;
					when others => --Never reached
						clk_state <= RESET;
				end case;
			end if;
		end if;
	end process;

	process (s00_axi_aclk)
		begin
		if (rising_edge(s00_axi_aclk)) then
			if (s00_axi_aresetn = '0') then
				enable_reg <= '0';
				sen_reg <= '0';
			 else
				if (clk_state = WAIT_EN and CTRL_REG(0) = '1') then
					sen_reg <= '1';
				else
					sen_reg <= '0';
				end if;
				if (clk_state = WAIT_RUN or clk_state = ENABLED) then
					enable_reg <= '1';
				else
					enable_reg <= '0';
				end if;
			end if;
		end if;
	end process;

Inst_vdma_to_vga: vdma_to_vga
	GENERIC MAP(
		C_S_AXIS_TDATA_WIDTH => C_S_AXIS_TDATA_WIDTH
	)
	PORT MAP(
		LOCKED_I => locked,
		ENABLE_I => enable_reg,
		RUNNING_O => vga_running,
		S_AXIS_ACLK => S_AXIS_ACLK,
		S_AXIS_TDATA => S_AXIS_TDATA,
		S_AXIS_TVALID => S_AXIS_TVALID,
		S_AXIS_TLAST => S_AXIS_TLAST,
		S_AXIS_TREADY => S_AXIS_TREADY,
		FSYNC_O => FSYNC_O,
		HSYNC_O => HSYNC_O,
		VSYNC_O => VSYNC_O,
		DE_O => DE_O,
		DATA_O => DATA_O,
		DEBUG_O => open,
		CTL_O => CTL_O,
		VGUARD_O => VGUARD_O,
		DGUARD_O => DGUARD_O,
		DIEN_O => DIEN_O,
		DIH_O => DIH_O,
		USR_HPS_I => HPARAM1_REG(27 downto 16),
		USR_HPE_I => HPARAM1_REG(11 downto 0),
		USR_HPOL_I => HPARAM2_REG(16),
		USR_HPREAMS_I => PREAM_REG(27 downto 16),
		USR_HPREAME_I => PREAM_REG(11 downto 0),
		USR_VGUARDS_I => VGUARD_REG(27 downto 16),
		USR_VGUARDE_I => VGUARD_REG(11 downto 0),
		USR_VDATAENS_I => VDATAEN_REG(27 downto 16),
		USR_VDATAENE_I => VDATAEN_REG(11 downto 0),
		USR_HDATAENS_I => HDATAEN_REG(27 downto 16),
		USR_HDATAENE_I => HDATAEN_REG(11 downto 0),
		USR_DATAENPOL_I => HDATAEN_REG(31),
		USR_HMAX_I => HPARAM2_REG(11 downto 0),
		USR_VPS_I => VPARAM1_REG(27 downto 16),
		USR_VPE_I => VPARAM1_REG(11 downto 0),
		USR_VPOL_I => VPARAM2_REG(16),
		USR_VMAX_I => VPARAM2_REG(11 downto 0),
		USR_FSYNC_I => FSYNC_REG(11 downto 0)
	);

	process (s00_axi_aclk)
	begin
		if (rising_edge(s00_axi_aclk)) then
			if (s00_axi_aresetn = '0') then
				STAT_REG(0) <= '0';
				vga_running_sync <= (others => '0');
			else
				vga_running_sync <= vga_running_sync(vga_running_sync'high - 1 downto vga_running_sync'low) & vga_running;
				STAT_REG(0) <= vga_running_sync(vga_running_sync'high);
			end if;
		end if;
	end process;

-- User logic ends

end arch_imp;
