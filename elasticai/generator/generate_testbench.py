def write_imports():
    return """library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;               -- for type conversions
    """


def write_entity():
    return """entity sigmoid_tb is
    port ( clk: out std_logic);
end entity ; -- sigmoid_tb
    """


def write_component(data_width, frac_width):
    return """architecture behav of sigmoid_tb is

    component sigmoid is
        generic (
                DATA_WIDTH : integer := {};
                FRAC_WIDTH : integer := {}
            );
        port (
            x : in signed(DATA_WIDTH-1 downto 0);
            y: out signed(DATA_WIDTH-1 downto 0)
        );
    end component;
    """.format(data_width, frac_width)


def write_inputs():
    return """    ------------------------------------------------------------
    -- Testbench Internal Signals
    ------------------------------------------------------------
    signal clk_period : time := 1 ns;
    signal test_input : signed(16-1 downto 0):=(others=>'0');
    signal test_output : signed(16-1 downto 0);
    """


def write_clock():
    return """begin

    clock_process : process
    begin
        clk <= '0';
        wait for clk_period/2;
        clk <= '1';
        wait for clk_period/2;
    end process; -- clock_process
    """


def write_utt():
    return """    utt: sigmoid
    port map (
    x => test_input,
    y => test_output
    );
    """


def write_test_process(testoutput_1281, testoutput_1000, testoutput_500):
    return """test_process: process is
    begin
        Report "======Simulation start======" severity Note;
        
        test_input <=  to_signed(-1281,16);
        wait for 1*clk_period;
        report "The value of 'test_output' is " & integer'image(to_integer(unsigned(test_output)));
        assert test_output={} report "The test case -1281 fail" severity failure;
        
        test_input <=  to_signed(-1000,16);
        wait for 1*clk_period;
        report "The value of 'test_output' is " & integer'image(to_integer(unsigned(test_output)));
        assert test_output={} report "The test case -1000 fail" severity failure;
        
        test_input <=  to_signed(-500,16);
        wait for 1*clk_period;
        report "The value of 'test_output' is " & integer'image(to_integer(unsigned(test_output)));
        assert test_output={} report "The test case -500 fail" severity failure;
        
        
        -- if there is no error message, that means all test case are passed.
        report "======Simulation Success======" severity Note;
        report "Please check the output message." severity Note;
        
        -- wait forever
        wait;
        
    end process; -- test_process

end behav ; -- behav
""".format(testoutput_1281, testoutput_1000, testoutput_500)


def main():
    with open('../testbench/sigmoid_generate_tb.vhd', 'w') as f:
        f.write(write_imports())
        f.write("\n")
        f.write(write_entity())
        f.write("\n")
        f.write(write_component(data_width=16, frac_width=8))
        f.write("\n")
        f.write(write_inputs())
        f.write("\n")
        f.write(write_clock())
        f.write("\n")
        f.write(write_utt())
        f.write("\n")
        f.write(write_test_process(0, 4, 28))


if __name__ == '__main__':
    main()
