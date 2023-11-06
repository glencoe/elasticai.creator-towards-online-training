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

    type t_state is (s_reset, s_data_transfer_MAC, s_MAC_compute, s_reset_mac, s_done);
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
            reset => mac_reset,
            next_sample => next_sample,
            x1 => x1,
            x2 => x2,
            sum => sum,
            done => done
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
            if enable = '1' AND state = s_reset then
                report("status conv1d: state = s_reset");
                mac_reset <= '0';
                -- start first MAC_Computation
                next_sample <= '1';
                state <= s_data_transfer_MAC;
            elsif enable = '1' AND state = s_data_transfer_MAC then
                report("status conv1d: state = s_data_transfer_MAC");
                mac_reset <= '0';
                report("status conv1d: Kernel " & to_bstring(kernel_counter));
                report("status conv1d: Input_Channel " & to_bstring(input_channel_counter));
                report("status conv1d: Output_Channel " & to_bstring(output_channel_counter));
                report("status conv1d: Input " & to_bstring(input_counter));
                if kernel_counter /= KERNEL_SIZE then

                    --write MAC input for next cycle
                    x_address <= resize(input_channel_counter * VECTOR_WIDTH + kernel_counter + input_counter, x_address'length);
                    w_address <= resize(input_channel_counter * VECTOR_WIDTH + kernel_counter, w_address'length);
                    x1 <= x;
                    x2 <= w;
                    state <= s_MAC_compute;
                    kernel_counter := kernel_counter + 1;
                elsif input_channel_counter /= IN_CHANNELS-1 then
                    kernel_counter := (others => '0');
                    input_channel_counter := input_channel_counter + 1;
                elsif output_channel_counter /= OUT_CHANNELS then
                    report("stauts conv1d: out_channels");
                    if bias_added = '0' then
                        b_address <= resize(output_channel_counter, b_address'length);
                        x1 <= FXP_ONE;
                        x2 <= b;
                        bias_added := '1';
                        state <= s_MAC_compute;
                    else
                        --read MAC output from last computation and write to y_ram
                        y_ram(to_integer(resize(output_channel_counter*(VECTOR_WIDTH-KERNEL_SIZE+1)+input_counter+kernel_counter, y_ram'length))) <= sum;
                        bias_added := '0';
                        input_channel_counter := (others => '0');
                        output_channel_counter := output_channel_counter + 1;
                        state <= s_reset_MAC;
                    end if;
                elsif input_counter /= VECTOR_WIDTH-KERNEL_SIZE-1 then
                    output_channel_counter := (others => '0');
                    input_counter := input_counter + 1;
                else
                    report("status conv1d: state = done");
                    state <= s_done;
                end if;
            elsif state = s_MAC_compute then
                report("status conv1d: state = s_MAC_compute");
                next_sample <= '0';
                state <= s_data_transfer_MAC;
            elsif state = s_done then
                done <= '1';
                --report("done: " & integer(done));
            elsif state = s_reset_MAC then
                report("status conv1d: state = s_reset_MAC");
                mac_reset <= '1';
                state <= s_data_transfer_MAC;
            end if;
        end if;
    end process main;

    y_writing : process (clock, state)
    begin
        if state=s_done then
            if falling_edge(clock) then
                -- After the layer in at idle mode, y is readable
                -- but it only update at the rising edge of the clock
                y <= y_ram(to_integer(unsigned(y_address)));
            end if;
        end if;
    end process y_writing;

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