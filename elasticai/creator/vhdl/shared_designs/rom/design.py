from creator.vhdl.code_generation.design_builder import DesignBuilder
from creator.vhdl.code_generation.language import (
    IEEE,
    Architecture,
    Direction,
    Entity,
    Port,
    Signal,
    Type,
    VectorType,
    VHDLPackage,
)

from elasticai.creator.file_generation.savable import Path
from elasticai.creator.file_generation.template import SimpleTemplate
from elasticai.creator.vhdl.code_generation.addressable import calculate_address_width
from elasticai.creator.vhdl.code_generation.code_abstractions import (
    to_vhdl_binary_string,
)


class _RomDirector:
    def __init__(
        self, name: str, addressing_strategy, data_type: VectorType, values
    ) -> None:
        self._builder = DesignBuilder()
        std_logic = Type("std_logic")
        self._num_values = len(values)
        self._data_width = data_type.width
        self._address_signal: Signal[VectorType] = addressing_strategy.get_signal(
            "addr", self._num_values
        )
        self._address_width = self._address_signal.type.width
        self._builder.entity = Entity(
            name=name,
            port=Port(
                signals=[
                    Signal(name="clk", direction=Direction.IN, type=std_logic),
                    Signal(name="en", direction=Direction.IN, type=std_logic),
                    self._address_signal,
                    Signal(name="data", direction=Direction.OUT, type=data_type),
                ]
            ),
        )
        self._builder.packages = [
            IEEE.STD_LOGIC_1164,
            IEEE.STD_LOGIC_UNSIGNED,
        ] + addressing_strategy.get_extra_packages()
        self._values = [
            to_vhdl_binary_string(x, self._data_width)
            for x in self._append_zeros_to_fill_addressable_memory(values)
        ]
        self._resource_option = "auto"
        conversion = addressing_strategy.get_conversion_function()
        self._builder.architecture = Architecture(
            "rtl",
            entity_name=name,
            decl=[
                (
                    f"type {name}_array_t is array (0 to "
                    f"2**{self._address_signal.type.width}-1) "
                    f"of {data_type};"
                ),
                f"signal ROM : {name}_array_t:=({','.join(self._values)});",
                "attribute rom_style : string;",
                f'attribute rom_style of ROM : signal is "{self._resource_option}";',
            ],
            impl=[
                "ROM_process: process(clk)",
                "begin",
                "    if rising_edge(clk) then",
                "        if (en = '1') then",
                f"            data <= ROM({conversion}(addr));",
                "        end if;",
                "    end if;",
                "end process ROM_process;",
            ],
        )

    def build(self) -> list[str]:
        return self._builder.build()

    def _append_zeros_to_fill_addressable_memory(self, values: list[int]) -> list[int]:
        missing_number_of_zeros = 2**self._address_width - len(values)
        return values + _pad_with_zeros(missing_number_of_zeros)


class StdLogicAddressing:
    def get_signal(self, name: str, num_values: int) -> Signal[VectorType]:
        width = calculate_address_width(num_values)
        return Signal(
            name, type=VectorType("std_logic_vector", width), direction=Direction.IN
        )

    def get_conversion_function(self) -> str:
        return "conv_integer"

    def get_extra_packages(self) -> list[VHDLPackage]:
        return []


class UnsignedAddressing:
    def get_signal(self, name: str, num_values: int) -> Signal[VectorType]:
        width = calculate_address_width(num_values)
        return Signal(
            name, type=VectorType("unsigned", width=width), direction=Direction.IN
        )

    def get_conversion_function(self) -> str:
        return "to_integer"

    def get_extra_packages(self) -> list[VHDLPackage]:
        return [IEEE.NUMERIC_STD]


class Rom:
    def __init__(
        self, name: str, data_width: int, values_as_integers: list[int]
    ) -> None:
        self._director = _RomDirector(
            name=name,
            data_type=VectorType("std_logic_vector", data_width),
            addressing_strategy=StdLogicAddressing(),
            values=values_as_integers,
        )

    def save_to(self, destination: Path) -> None:
        template = SimpleTemplate(content=self._director.build(), parameters={})
        destination.as_file(".vhd").write(template)


class RomWithUnsignedAddressAndSignedData:
    def __init__(self, name: str, data_width: int, values_as_integers: list[int]):
        self._director = _RomDirector(
            name=name,
            data_type=VectorType("signed", data_width),
            addressing_strategy=UnsignedAddressing(),
            values=values_as_integers,
        )

    def save_to(self, destination: Path) -> None:
        template = SimpleTemplate(content=self._director.build(), parameters={})
        destination.as_file(".vhd").write(template)


def _pad_with_zeros(n: int) -> list[int]:
    return [0] * n
