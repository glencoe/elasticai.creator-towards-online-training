library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;
use ieee.std_logic_textio.all;
use std.env.finish;


entity testbench_fxp_mac is
end testbench_fxp_mac;

architecture Behavioral of testbench_fxp_mac is
    constant TOTAL_WIDTH : integer := $total_width;
    signal clock_period : time := 2 ps;
    signal clock : std_logic := '0';
    signal reset : std_logic := '0';
    signal next_sample : std_logic;
    signal x1 : signed (TOTAL_WIDTH-1 downto 0) := (others => '0');
    signal x2 : signed (TOTAL_WIDTH-1 downto 0) := (others => '0');
    signal sum :  signed(TOTAL_WIDTH-1 downto 0);
    signal done :  std_logic;

    type input_array_t is array (0 to 1) of signed(TOTAL_WIDTH-1 downto 0);
    signal x1_values : input_array_t := ($x1);
    signal x2_values : input_array_t := ($x2);



begin
    UUT : entity work.${uut_name}
    port map (reset => reset, next_sample => next_sample, x1 => x1, x2 => x2, sum => sum, done => done);

    clock <= not clock after clock_period/2;

    testbench_1 : process(clock, done)
      variable iteration_id : integer := 0;
      variable reset_performed : std_logic := '0';
      variable value_id : integer := 0;
      constant max_iterations : integer := 5;
      constant max_values : integer := $vector_width;
      type TYPE_STATE is (s_reset, s_start_computation, s_data_transfer_MAC, s_wait_for_computation_done, s_finish_simulation);
      variable test_state : TYPE_STATE := s_reset;
    begin
        if test_state = s_reset then
            reset <= '1';
            test_state := s_start_computation;
            next_sample <= '0';
        elsif test_state = s_start_computation then
            reset <= '0';
            test_state := s_data_transfer_MAC;
        elsif test_state = s_data_transfer_MAC then
            next_sample <= '0';
            test_state := s_wait_for_computation_done;
            if done = '0' and value_id < max_values then
                x1 <= x1_values(value_id);
                x2 <= x2_values(value_id);
                value_id := value_id + 1;
            elsif done = '1' then
                report("result: " & to_bstring(sum));
                test_state := s_finish_simulation;
            end if;
        elsif test_state = s_wait_for_computation_done then
            next_sample <= '1';
            test_state := s_data_transfer_MAC;
        elsif test_state = s_finish_simulation then
            finish;
        end if;
    end process;

    end_after_100cycles : process (clock)
    variable i : integer range 0 to 10000;
    begin
        if rising_edge(clock) then
            if i = 100 then
                report("OUT of TIME");
                finish;
            else
                i := i + 1;
            end if;
        end if;
    end process;
end Behavioral;
