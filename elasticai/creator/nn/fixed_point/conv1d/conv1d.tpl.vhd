library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity ${name} is
    port (
        enable : in std_logic;
        reset : in std_logic;
        x : in signed(${total_width}-1 downto 0);
        x_address : out signed(${x_address_width}-1 downto 0);
        y : out signed(${total_width}-1 downto 0);
        y_address : in signed(${y_address_width}-1 downto 0);
        done : out std_logic := '0'
    );
end;

architecture rtl of ${name} is
    constant TOTAL_WIDTH : natural := ${total_width};
    constant FRAC_WIDTH : natural := ${frac_width};
    constant VECTOR_WIDTH : natural := ${vector_width};
    constant KERNEL_SIZE : natural := ${kernel_size};
    constant IN_CHANNELS : natural := ${in_channels};
    constant OUT_CHANNELS : natural := ${out_channels};
begin

end;

