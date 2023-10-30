library ieee;

use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity conv1d_fxp_MAC_RoundToZero is
    generic (
        TOTAL_WIDTH : natural;
        FRAC_WIDTH : natural;
        VECTOR_WIDTH : natural;
        KERNEL_SIZE : natural;
        IN_CHANNELS : natural;
        OUT_CHANNELS : natural;
        X_ADDRESS_WIDTH : natural;
        Y_ADDRESS_WIDTH : natural
    );
    port (
        clock : in std_logic;
        enable : in std_logic;
        reset : in std_logic;
        x : in signed(TOTAL_WIDTH-1 downto 0);
        x_address : out unsigned(X_ADDRESS_WIDTH-1 downto 0);
        y : out signed(TOTAL_WIDTH-1 downto 0);
        y_address : in unsigned(Y_ADDRESS_WIDTH-1 downto 0);
        done : out std_logic := '0'
    );
end;

architecture rtl of conv1d_fxp_MAC_RoundToZero is
    constant FXP_ONE : signed(TOTAL_WIDTH-1 downto 0) := to_signed(2**FRAC_WIDTH,TOTAL_WIDTH);

    signal next_sample : std_logic;
    signal x1 : signed(TOTAL_WIDTH-1 downto 0);
    signal x2 : signed(TOTAL_WIDTH-1 downto 0);
    signal sum : signed(TOTAL_WIDTH-1 downto 0);
    signal mac_done : std_logic;
    type data is array (0 to OUT_CHANNELS*VECTOR_WIDTH-1) of signed(TOTAL_WIDTH-1 downto 0);
    signal y_ram : data;

    signal n_clock : std_logic;
    signal w_in : std_logic_vector(TOTAL_WIDTH-1 downto 0);
    signal b_in : std_logic_vector(TOTAL_WIDTH-1 downto 0);
    signal addr_w : std_logic_vector(OUT_CHANNELS*IN_CHANNELS*KERNEL_SIZE-1 downto 0); -- too big round(log2())
    signal addr_b : std_logic_vector(OUT_CHANNELS*IN_CHANNELS-1 downto 0); -- too big round(log2())

    type t_state is (s_reset, s_computing, s_done);
    signal state : t_state;
begin
    -- connecting signals to ports
    n_clock <= not clock;


    conv1d_fxp_MAC : entity work.fxp_MAC_RoundToZero
        generic map(
            VECTOR_WIDTH => VECTOR_WIDTH,
            TOTAL_WIDTH => TOTAL_WIDTH,
            FRAC_WIDTH => FRAC_WIDTH
        )
        port map (
            reset => reset,
            next_sample => next_sample,
            x1 => x1,
            x2 => x2,
            sum => sum,
            done => done
        );

    process (clock)
        variable var_kernel_counter : unsigned(KERNEL_SIZE-1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable var_input_counter : unsigned(VECTOR_WIDTH-1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable var_input_channel_counter : unsigned(IN_CHANNELS-1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable var_output_channel_counter : unsigned(OUT_CHANNELS-1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
    begin
        if reset = '1' then
            addr_w <= (others => '0');
            addr_b <= (others => '0');
            var_kernel_counter := (others => '0');
            var_input_counter := (others => '0');
            var_input_channel_counter := (others => '0');
            var_output_channel_counter := (others => '0');
            done <= '0';
            state <= s_reset;
        else
            if enable = '1' AND state = s_computing then
                if var_input_counter /= VECTOR_WIDTH-1 then
                    if var_output_channel_counter /= OUT_CHANNELS-1 then
                        if var_input_channel_counter /= IN_CHANNELS-1 then
                            if var_kernel_counter /= KERNEL_SIZE-1 then


                                var_kernel_counter := var_kernel_counter + 1;
                            end if;
                            var_input_channel_counter := var_input_channel_counter + 1;
                        end if;
                        var_output_channel_counter := var_output_channel_counter + 1;
                    end if;
                    var_input_counter := var_input_counter + 1;
                end if;
            end if;
        end if;
    end process;

    y_reading : process (clock, state)
    begin
        if state=s_done then
            if falling_edge(clock) then
                -- After the layer in at idle mode, y is readable
                -- but it only update at the rising edge of the clock
                y <= y_ram(to_integer(unsigned(y_address)));
            end if;
        end if;
    end process y_reading;

    -- Weights
    rom_w : entity work.conv1d_w_rom(rtl)
    port map  (
        clk  => n_clock,
        en   => '1',
        addr => addr_w,
        data => w_in
    );

    -- Bias
    rom_b : entity work.conv1d_b_rom(rtl)
    port map  (
        clk  => n_clock,
        en   => '1',
        addr => addr_b,
        data => b_in
    );

end;