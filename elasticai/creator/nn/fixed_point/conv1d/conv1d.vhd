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

    signal mac_reset : std_logic;
    signal next_sample : std_logic;
    signal x1 : signed(TOTAL_WIDTH-1 downto 0);
    signal x2 : signed(TOTAL_WIDTH-1 downto 0);
    signal sum : signed(TOTAL_WIDTH-1 downto 0);
    signal mac_done : std_logic;
    type data is array (0 to OUT_CHANNELS*(VECTOR_WIDTH-KERNEL_SIZE+1)*KERNEL_SIZE-1) of signed(TOTAL_WIDTH-1 downto 0);
    signal y_ram : data;

    signal n_clock : std_logic;
    signal w : signed(TOTAL_WIDTH-1 downto 0);
    signal b : signed(TOTAL_WIDTH-1 downto 0);
    signal w_address : unsigned(0 downto 0); -- too big round(log2())
    signal b_address : unsigned(0 downto 0); -- too big round(log2())

    type t_state is (s_reset, s_data_transfer_MAC, s_MAC_mul_x_w, s_MAC_add_b, s_MAC_get_result, s_reset_mac, s_done);
    signal state : t_state;
begin
    -- connecting signals to ports
    n_clock <= not clock;


    conv1d_fxp_MAC : entity work.fxp_MAC_RoundToZero
        generic map(
            VECTOR_WIDTH => KERNEL_SIZE*IN_CHANNELS,
            TOTAL_WIDTH => TOTAL_WIDTH,
            FRAC_WIDTH => FRAC_WIDTH
        )
        port map (
            reset => mac_reset,
            next_sample => next_sample,
            x1 => x1,
            x2 => x2,
            sum => sum,
            done => mac_done
        );

    main : process (clock)
        variable kernel_counter : unsigned(0+1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable input_counter : unsigned(1+1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable input_channel_counter : unsigned(0+1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable output_channel_counter : unsigned(0+1 downto 0); -- too big integer(round(log2(var-1)) downto 0)
        variable bias_added : std_logic;
    begin
        if reset = '1' then
            -- reset such that MAC_enable triggers MAB_enable directly
            x_address <= (others => '0');
            w_address <= (others => '0');
            b_address <= (others => '0');
            kernel_counter := (others => '0');
            input_counter := (others => '0');
            input_channel_counter := (others => '0');
            output_channel_counter := (others => '0');
            bias_added := '0';
            next_sample <= '0';
            done <= '0';
            mac_reset <= '1';
            state <= s_reset;
        else
            if rising_edge(clock) then
                if enable = '1' AND state = s_reset then
                    report("debug: conv1d: state = s_reset");
                    mac_reset <= '0';
                    -- start first MAC_Computation
                    --next_sample <= '1';
                    state <= s_data_transfer_MAC;
                elsif enable = '1' AND state = s_data_transfer_MAC then
                    report("debug: conv1d: state = s_data_transfer_MAC");
                    mac_reset <= '0';
                    next_sample <= '0';
                    if input_counter /= VECTOR_WIDTH-KERNEL_SIZE+1 then
                        if output_channel_counter /= OUT_CHANNELS then
                            if input_channel_counter /= IN_CHANNELS then
                                if kernel_counter /= KERNEL_SIZE then
                                    report("debug: conv1d: Input   output_c    input_c     kernel");
                                    report("debug: conv1d: " & to_bstring(input_counter) &"     "& to_bstring(output_channel_counter) &"          " & to_bstring(input_channel_counter)  & "          " & to_bstring(kernel_counter));
                                    x_address <= resize(input_channel_counter * VECTOR_WIDTH + kernel_counter + input_counter, x_address'length);
                                    w_address <= resize(input_channel_counter * VECTOR_WIDTH + kernel_counter, w_address'length);
                                    state <= s_MAC_mul_x_w;
                                    kernel_counter := kernel_counter + 1;
                                else
                                    kernel_counter := (others => '0');
                                    input_channel_counter := input_channel_counter + 1;
                                end if;
                            elsif bias_added = '0' then
                                report("debug: conv1d: add bias");
                                bias_added := '1';
                                state <= s_MAC_add_b;
                            elsif bias_added = '1' then
                                --read MAC output from last computation and write to y_ram
                                bias_added := '0';
                                state <= s_MAC_get_result;
                                kernel_counter := (others => '0');
                                input_channel_counter := (others => '0');
                                output_channel_counter := output_channel_counter + 1;
                            end if;
                        else
                            kernel_counter := (others => '0');
                            input_channel_counter := (others => '0');
                            output_channel_counter := (others => '0');
                            input_counter := input_counter + 1;
                        end if;
                    else
                        state <= s_done;
                    end if;
                elsif state = s_MAC_mul_x_w or state = s_MAC_add_b then
                    report("debug: conv1d: state = mul_x or add_b" );
                    next_sample <= '1';
                    state <= s_data_transfer_MAC;
                elsif state = s_MAC_get_result then
                    report("debug: conv1d: state = s_MAC_get_result");
                    next_sample <= '1';
                    if mac_done = '1' then
                        report("debug: conv1d: mac: done");
                        next_sample <= '0';
                        report("debug: conv1d: write sum to y_ram");
                        y_ram(to_integer(resize((output_channel_counter-1)*(VECTOR_WIDTH-KERNEL_SIZE+1)+input_counter, y_ram'length))) <= sum;
                        state <= s_reset_MAC;
                    end if;
                elsif state = s_done then
                    --report("debug: conv1d: state = s_done");
                    done <= '1';
                elsif state = s_reset_MAC then
                    report("debug: conv1d: state = s_reset_MAC");
                    mac_reset <= '1';
                    state <= s_data_transfer_MAC;
                end if;
            end if;
        end if;
    end process main;

    y_writing : process (clock, state)
    begin
        if state = s_done then
            if falling_edge(clock) then
                -- After the layer in at idle mode, y is readable
                -- but it only update at the falling edge of the clock
                y <= y_ram(to_integer(unsigned(y_address)));
            end if;
        end if;
    end process y_writing;
    
    write_MAC_inputs : process (clock, state)
    begin
        if rising_edge(clock) then
            if state = s_MAC_mul_x_w then
                x1 <= x;
                x2 <= w;
            elsif state = s_MAC_add_b then
                x1 <= FXP_ONE;
                x2 <= b;
            end if;
        end if;
    end process write_MAC_inputs;
    
    -- Weights
    rom_w : entity work.conv1d_w_rom(rtl)
    port map  (
        clk  => n_clock,
        en   => '1',
        addr => w_address,
        data => w
    );

    -- Bias
    rom_b : entity work.conv1d_b_rom(rtl)
    port map  (
        clk  => n_clock,
        en   => '1',
        addr => b_address,
        data => b
    );

end;