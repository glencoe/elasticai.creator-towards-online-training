library ieee;
    use ieee.std_logic_1164.all;
    use ieee.std_logic_unsigned.all;
    use ieee.numeric_std.all;
entity ${name} is
    port (
        clk : in std_logic;
        en : in std_logic;
        addr : in unsigned(${rom_addr_bitwidth}-1 downto 0);
        data : out signed(${rom_data_bitwidth}-1 downto 0)
    );
end entity ${name};
architecture rtl of ${name} is
    type ${name}_array_t is array (0 to 2**${rom_addr_bitwidth}-1) of signed(${rom_data_bitwidth}-1 downto 0);
    signal ROM : ${name}_array_t:=(${rom_value});
    attribute rom_style : string;
    attribute rom_style of ROM : signal is "${resource_option}";
begin
    ROM_process: process(clk)
    begin
        if rising_edge(clk) then
            if (en = '1') then
                data <= ROM(to_integer(addr));
            end if;
        end if;
    end process ROM_process;
end architecture rtl;
