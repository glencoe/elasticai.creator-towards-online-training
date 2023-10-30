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
    --CLOCK
    signal clock_period : time := 2 ps;


    --DATA INPUT
    type data is array (0 to ${signal_length}-1) of signed(${total_bits}-1 downto 0);
    signal data_in : data;
    file input_file : text;
    signal read_done: std_logic := '0';

    --UUT
    signal clock : std_logic;
    signal enable : std_logic;
    signal reset : std_logic;
    signal x : signed(${total_bits}-1 downto 0);
    signal x_address : signed(${x_address_width}-1 downto 0);
    signal y : signed(${total_bits}-1 downto 0);
    signal y_address : signed(${y_address_width}-1 downto 0);
    signal done : std_logic := '0';

begin
    UUT : entity work.${uut_name}
    port map (clock => clock, enable => enable, reset => reset, x => x, x_address => x_address, y => y, y_address => y_address, done => done);

    clk : process
    begin
        clock <= not clock;
        wait for clock_period/2;
    end process;

    read_inputs_to_buffer : process (read_done)
        variable v_ILINE     : line;
        variable v_in : signed(${total_bits}-1 downto 0);
        variable v_SPACE     : character;
    begin
        report "reading file " & INPUTS_FILE_PATH;

        if read_done = '0' then
            file_open(input_file, INPUTS_FILE_PATH,  read_mode);
            readline(input_file, v_ILINE);
            while not endfile(input_file) loop
                readline(input_file, v_ILINE); -- read header

                for i in 0 to ${signal_length}-1 loop
                    read(v_ILINE, v_in); -- read values
                    if i /= ${signal_length}-1 then -- check if not last item of row
                        read(v_ILINE, v_SPACE);
                    end if;
                    data_in(i) <= v_in;
                end loop;
                read_done <= '1';
            end loop;
        end if;
    end process;

    start_test : process(clock, read_done)
        variable test_return_signal : signed (${total_bits}-1 downto 0) := (others => '1');
    begin
        if read_done = '1' then
            report "result: " & to_bstring(test_return_signal);
            report "result: " & to_bstring(test_return_signal);
            report "result: " & to_bstring(test_return_signal);
            finish;
        end if;
    end process;


end;