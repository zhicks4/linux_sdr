----------------------------------------------------------------------------------
-- EN 525.742 Lab 6
-- Z. Hicks
-- 4/1/2023
-- 
-- DDC Implementation using DDS, complex multiplier, and FIR filters
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.all;


entity ddc is
    Port (
        clk : in STD_LOGIC;
        resetn : in STD_LOGIC;
        -- ADC Input
        adc_dds_phase_inc_data : in STD_LOGIC_VECTOR(31 downto 0);
        -- Mixer Input
        mixer_dds_phase_inc_data : in STD_LOGIC_VECTOR(31 downto 0);
        -- Filter Output
        m_axis_data_tvalid : out STD_LOGIC;
        m_axis_data_tdata : out STD_LOGIC_VECTOR(31 downto 0)
    );
end ddc;

architecture Behavioral of ddc is

    ------------------------------------------------------------
    ------------------------ Components ------------------------
    ------------------------------------------------------------
     
    -- ADC DDS
    component dds_compiler_0
        port (
            aclk : IN STD_LOGIC;
            aresetn : IN STD_LOGIC;
            s_axis_phase_tvalid : IN STD_LOGIC;
            s_axis_phase_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            m_axis_data_tvalid : OUT STD_LOGIC;
            m_axis_data_tdata : OUT STD_LOGIC_VECTOR(15 DOWNTO 0) -- cosine (15 downto 0)
        );
    end component; 
     
    -- Mixer DDS
    component dds_compiler_1
        port (
            aclk : IN STD_LOGIC;
            aresetn : IN STD_LOGIC;
            s_axis_phase_tvalid : IN STD_LOGIC;
            s_axis_phase_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            m_axis_data_tvalid : OUT STD_LOGIC;
            m_axis_data_tdata : OUT STD_LOGIC_VECTOR(31 DOWNTO 0)
        );
    end component;
    
    -- Mixer Complex Multiplier
    component cmpy_0
        port (
            aclk : IN STD_LOGIC;
            s_axis_a_tvalid : IN STD_LOGIC;
            s_axis_a_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            s_axis_b_tvalid : IN STD_LOGIC;
            s_axis_b_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            m_axis_dout_tvalid : OUT STD_LOGIC;
            m_axis_dout_tdata : OUT STD_LOGIC_VECTOR(79 DOWNTO 0)
        );
    end component;
    
    -- FIR Filter 1
    component filter_1
        port (
            aclk : IN STD_LOGIC;
            s_axis_data_tvalid : IN STD_LOGIC;
            s_axis_data_tready : OUT STD_LOGIC;
            s_axis_data_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0); -- path 0 (15 downto 0), path 1 (31 downto 16)
            m_axis_data_tvalid : OUT STD_LOGIC;
            m_axis_data_tdata : OUT STD_LOGIC_VECTOR(47 DOWNTO 0) -- path 0 (40 downto 24), path 1 (16 downto 0)
        );
    end component;
    
    -- FIR Filter 2
    component filter_2
        port (
            aclk : IN STD_LOGIC;
            s_axis_data_tvalid : IN STD_LOGIC;
            s_axis_data_tready : OUT STD_LOGIC;
            s_axis_data_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            m_axis_data_tvalid : OUT STD_LOGIC;
            m_axis_data_tdata : OUT STD_LOGIC_VECTOR(47 DOWNTO 0)
        );
    end component;
    
    -- ILA
--    component ila_0 is
--        port (
--            clk : IN STD_LOGIC;
--            probe0 : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
--            probe1 : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
--            probe2 : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
--            probe3 : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
--            probe4 : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
--            probe5 : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
--            probe6 : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
--            probe7 : IN STD_LOGIC_VECTOR(0 DOWNTO 0);
--            probe8 : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
--            probe9 : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
--            probe10 : IN STD_LOGIC_VECTOR(0 DOWNTO 0)
--        );
--    end component;
    
    ------------------------------------------------------------
    ------------------------- Signals --------------------------
    ------------------------------------------------------------
       
    signal mixer_dds_valid : STD_LOGIC;
    signal mixer_dds_out : STD_LOGIC_VECTOR(31 downto 0);
    signal mixer_cos : STD_LOGIC_VECTOR(15 downto 0);
    signal mixer_sin : STD_LOGIC_VECTOR(15 downto 0);
    
    -- Mixer signals
    signal adc_dds_valid : STD_LOGIC;
    signal adc_dds_out : STD_LOGIC_VECTOR(15 downto 0);
    signal adc_mult_in : STD_LOGIC_VECTOR(31 downto 0);
    signal mult_out : STD_LOGIC_VECTOR(79 downto 0);
    signal mult_out_I : STD_LOGIC_VECTOR(15 downto 0);
    signal mult_out_Q : STD_LOGIC_VECTOR(15 downto 0);
    signal mult_valid : STD_LOGIC;
    
    -- FIR filter signals
    signal filter_in_I : STD_LOGIC_VECTOR(15 downto 0);
    signal filter_in_Q : STD_LOGIC_VECTOR(15 downto 0);
    signal filter_1_in : STD_LOGIC_VECTOR(31 downto 0);
    signal filter_1_valid : STD_LOGIC;
    signal filter_1_out : STD_LOGIC_VECTOR(47 downto 0);
    signal filter_2_in : STD_LOGIC_VECTOR(31 downto 0);
    signal filter_2_valid : STD_LOGIC;
    signal filter_2_out : STD_LOGIC_VECTOR(47 downto 0);
    signal filtered_I : STD_LOGIC_VECTOR(15 downto 0);
    signal filtered_Q : STD_LOGIC_VECTOR(15 downto 0);

begin

    adc_dds : dds_compiler_0
    port map (
        aclk => clk,
        aresetn => resetn,
        s_axis_phase_tvalid => '1',
        s_axis_phase_tdata => adc_dds_phase_inc_data,
        m_axis_data_tvalid => adc_dds_valid,
        m_axis_data_tdata => adc_dds_out
    );
    
    mixer_lo : dds_compiler_1
    port map (
        aclk => clk,
        aresetn => resetn,
        s_axis_phase_tvalid => '1',
        s_axis_phase_tdata => mixer_dds_phase_inc_data,
        m_axis_data_tvalid => mixer_dds_valid,
        m_axis_data_tdata => mixer_dds_out
    );
    
    mixer_multiplier : cmpy_0
    port map (
        aclk => clk,
        s_axis_a_tvalid => adc_dds_valid,
        s_axis_a_tdata => adc_mult_in,
        s_axis_b_tvalid => mixer_dds_valid,
        s_axis_b_tdata => mixer_dds_out,
        m_axis_dout_tvalid => mult_valid,
        m_axis_dout_tdata => mult_out
    );
    
    filter1 : filter_1
    port map (
        aclk => clk,
        s_axis_data_tvalid => mult_valid,
        s_axis_data_tready => open,
        s_axis_data_tdata => filter_1_in,
        m_axis_data_tvalid => filter_1_valid,
        m_axis_data_tdata => filter_1_out
    );
    
    filter2: filter_2
    port map (
        aclk => clk,
        s_axis_data_tvalid => filter_1_valid,
        s_axis_data_tready => open,
        s_axis_data_tdata => filter_2_in,
        m_axis_data_tvalid => filter_2_valid,
        m_axis_data_tdata => filter_2_out
    );
    
--    ila_ddc : ila_0
--    port map (
--        clk => clk,
--        probe0 => adc_dds_data,
--        probe1(0) => adc_dds_valid,
--        probe2 => mixer_dds_out,
--        probe3(0) => mixer_dds_valid,
--        probe4 => filter_1_in,
--        probe5(0) => mult_valid,
--        probe6 => filter_2_in,
--        probe7(0) => filter_1_valid,
--        probe8 => filtered_I,
--        probe9 => filtered_Q,
--        probe10(0) => filter_2_valid
--    );
    
    -- Mixer
    adc_mult_in <= x"0000" & adc_dds_out;
    mixer_cos <= mixer_dds_out(15 downto 0);
    mixer_sin <= mixer_dds_out(31 downto 16);
    mult_out_I <= mult_out(29 downto 14);
    mult_out_Q <= mult_out(69 downto 54);
    
    -- Filters
    filter_1_in <= mult_out_Q & mult_out_I;
    filter_2_in <= filter_1_out(39 downto 24) & filter_1_out(15 downto 0);
    
    filtered_I <= filter_2_out(15 downto 0);
    filtered_Q <= filter_2_out(39 downto 24);
    
    m_axis_data_tdata <= filtered_Q & filtered_I;
    m_axis_data_tvalid <= filter_2_valid;

end Behavioral;
