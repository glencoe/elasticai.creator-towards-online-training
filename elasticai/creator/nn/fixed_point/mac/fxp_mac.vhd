library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity fxp_MAC_RoundToZero is
    generic (
        VECTOR_WIDTH : integer;
        TOTAL_WIDTH : integer;
        FRAC_WIDTH : integer;
        ACCUMULATOR_FACTOR: integer := 2
    );
    port (
        reset : in std_logic;
        next_sample : in std_logic;
        x1 : in signed(TOTAL_WIDTH-1 downto 0);
        x2 : in signed(TOTAL_WIDTH-1 downto 0);
        sum : out signed(TOTAL_WIDTH-1 downto 0) := (others => '0');
        done : out std_logic := '0'
    );
end;

architecture rtl of fxp_Mac_RoundToZero is

    function cut_down(x : in signed(ACCUMULATOR_FACTOR*TOTAL_WIDTH-1 downto 0)) return signed is
        variable result : signed(TOTAL_WIDTH-1 downto 0) := (others=>'0');
        constant left_bit : natural := TOTAL_WIDTH-1+FRAC_WIDTH;
        constant right_bit : natural := FRAC_WIDTH;
        constant max : signed(left_bit downto 0) := ('0', others => '1');
        constant min : signed(left_bit downto 0) := ('1', others => '0');
        variable dropped_fractional_part : signed(FRAC_WIDTH-1 downto 0);
    begin
        -- get result-range of x and underflow part
        result := x(left_bit downto right_bit);
        dropped_fractional_part := x(right_bit-1 downto 0);

        -- round negative towards zero
        if FRAC_WIDTH > 0 and result < 0 and dropped_fractional_part /= 0 then
            result := result + 1;
        end if;

        if x < 0 and result >= 0 then
            result := min(left_bit downto right_bit);
        elsif x >= 0 and result < 0 then
            result := max(left_bit downto right_bit);
        end if;
        return result;
    end function;

begin
    mac : process (next_sample, reset)
        variable accumulator : signed(ACCUMULATOR_FACTOR*TOTAL_WIDTH-1 downto 0) := (others=>'0');
        variable vector_idx : integer := 0;
        type t_state is (s_compute, s_finished);
        variable state : t_state := s_compute;
    begin
        if reset = '1' then
            accumulator := (others => '0');
            vector_idx := 0;
            state := s_compute;
            done <= '0';
            sum <= (others => '0');
            report("debug: MAC: reset");
        else
            --report("debug: MAC: accumulator pre-computation" & to_bstring(accumulator));

            if rising_edge(next_sample) then
                if state=s_compute then
                    --report("debug: MAC: state=s_compute");
                    report("debug: MAC: x1    x2");
                    report("debug: MAC: " & to_bstring(x1) & " " & to_bstring(x2));
                    accumulator := resize(x1*x2 + accumulator, accumulator'length);
                    report("debug: MAC: accumulator post-computation " & to_bstring(accumulator));
                    vector_idx := vector_idx + 1;
                    if vector_idx = VECTOR_WIDTH then
                       report("debug: MAC: cutdown");
                       sum <= cut_down(accumulator);
                       report("debug: MAC: accumulator post-computation " & to_bstring(accumulator));
                       state := s_finished;
                       done <= '1';
                    end if;
                end if;
            end if;
        end if;
    end process mac;
end rtl;
