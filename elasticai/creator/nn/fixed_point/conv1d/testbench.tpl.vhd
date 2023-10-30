library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;
use ieee.std_logic_textio.all;
use std.env.finish;

entity ${testbench_name} is
  generic (
      INPUTS_FILE_PATH: string
  );
end;

architecture rtl of ${testbench_name} is
    -- Test
    type TYPE_STATE is (s_prepare_uut_input, s_reset, s_start_computation, s_write_uut_output_address, s_read_uut_output, s_finish_simulation);
    signal test_state : TYPE_STATE := s_prepare_uut_input;
    signal trigger_start_up : std_logic := '0';

    --CLOCK
    signal clock_period : time := 2 ps;

    --DATA INPUT
    type data is array (0 to ${input_signal_length}-1) of signed(${total_bits}-1 downto 0);
    signal data_in : data;
    file input_file : text;
    signal input_cycles : signed(7 downto 0); --max for 255 lines of inputs
    signal end_of_file : std_logic := '0';

    --UUT
    signal clock : std_logic;
    signal enable : std_logic := '0';
    signal reset : std_logic := '1';
    signal x : signed(${total_bits}-1 downto 0);
    signal x_address : unsigned(${x_address_width}-1 downto 0);
    signal y : signed(${total_bits}-1 downto 0);
    signal y_address : unsigned(${y_address_width}-1 downto 0);
    signal done : std_logic := '0';

begin
    UUT : entity work.${uut_name}
    port map (clock => clock, enable => enable, reset => reset, x => x, x_address => x_address, y => y, y_address => y_address, done => done);

    clk : process
    begin
        clock <= not clock;
        wait for clock_period/2;
        trigger_start_up <= '1';
    end process;

    read_inputs_to_buffer : process
        variable v_ILINE     : line;
        variable v_in : signed(${total_bits}-1 downto 0);
        variable v_SPACE     : character;
    begin
        report "reading file " & INPUTS_FILE_PATH;
        if trigger_start_up = '1' then
            if test_state = s_prepare_uut_input then
                file_open(input_file, INPUTS_FILE_PATH,  read_mode);
                readline(input_file, v_ILINE);
                while not endfile(input_file) loop
                    readline(input_file, v_ILINE); -- read header

                    for i in 0 to ${input_signal_length}-1 loop
                        read(v_ILINE, v_in); -- read values
                        if i /= ${input_signal_length}-1 then -- check if not last item of row
                            read(v_ILINE, v_SPACE);
                        end if;
                        data_in(i) <= v_in;
                    end loop;
                    test_state <= s_reset;
                    wait until test_state = s_prepare_uut_input;
                    input_cycles <= input_cycles + 1;
                end loop;
                end_of_file <= '0';
            end if;
        end if;
    end process;

    start_test : process (clock)
        variable test_return_signal : signed (${total_bits}-1 downto 0) := (others => '1');
    begin
        if test_state = s_reset then
            reset <= '1';
            enable <= '0';
            test_state <= s_start_computation;
            y_address <= (others => '0');
        elsif test_state = s_start_computation then
            reset <= '0';
            enable <= '1';
            x <= data_in(to_integer(unsigned(x_address)));
            if done = '1' then
                test_state <= s_write_uut_output_address;
                y_address <= y_address - 1;
            end if;
        elsif test_state = s_write_uut_output_address then
            y_address <= y_address + 1;
            test_state <= s_read_uut_output;
        elsif test_state = s_read_uut_output then
            report "result: " & to_bstring(input_cycles) & "," & to_bstring(y);
            if y_address /= ${output_signal_length}-1 then
                test_state <= s_write_uut_output_address;
            elsif end_of_file = '0' then
                test_state <= s_prepare_uut_input;
            else
                test_state <= s_finish_simulation;
            end if;
        elsif test_state = s_finish_simulation then
            finish;
        end if;
    end process;


end;