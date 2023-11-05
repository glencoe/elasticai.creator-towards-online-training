from dataclasses import dataclass
from enum import auto, Enum, StrEnum
from typing import TypeVar, Generic, Any

from elasticai.creator.file_generation.savable import Path
from elasticai.creator.file_generation.template import (
    InProjectTemplate,
    module_to_package, SimpleTemplate,
)
from elasticai.creator.vhdl.code_generation.addressable import calculate_address_width
from elasticai.creator.vhdl.code_generation.code_abstractions import (
    to_vhdl_binary_string,
)


@dataclass(frozen=True)
class VHDLPackage:
    name: str
    library: str


class Library(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return VHDLPackage(name=name.lower(), library="ieee")


class IEEE:
    STD_LOGIC_1164 = VHDLPackage("std_logic_1164", library="ieee")
    STD_LOGIC_UNSIGNED = VHDLPackage("std_logic_unsigned", library="ieee")
    STD_LOGIC_SIGNED = VHDLPackage("std_logic_signed", library="ieee")
    NUMERIC_STD = VHDLPackage("numeric_std", library="ieee")


class Direction(StrEnum):
    IN = auto()
    OUT = auto()


@dataclass(frozen=True, eq=True)
class VectorType:
    name: str
    width: int

    def __str__(self):
        return f"{self.name}({self.width} - 1 downto 0)"


@dataclass(frozen=True, eq=True)
class Type:
    name: str

    def __str__(self) -> str:
        return self.name


T = TypeVar("T", VectorType, Type)


@dataclass(frozen=True, eq=True)
class Signal(Generic[T]):
    name: str
    direction: Direction
    type: T

    def __str__(self) -> str:
        return f"{self.name} : {self.direction.value} {self.type}"


@dataclass(frozen=True, eq=True)
class Port:
    signals: list[Signal]

    def build_code(self) -> list[str]:
        code = ["port ("]
        for signal in self.signals[:-1]:
            code.append(f"    {signal};")
        code.append(f"    {self.signals[-1]}")
        code.append(");")
        return code


@dataclass(frozen=True, eq=True)
class Entity:
    name: str
    port: Port

    def build_code(self) -> list[str]:
        code = [f"entity {self.name} is"]
        for line in self.port.build_code():
            code.append(f"    {line}")
        code.append(f"end entity {self.name};")
        return code


@dataclass(frozen=True, eq=True)
class Architecture:
    name: str
    entity_name: str
    decl: list[str]
    impl: list[str]

    def build_code(self) -> list[str]:
        code = [f"architecture {self.name} of {self.entity_name} is"]
        for line in self.decl:
            code.append(f"    {line}")
        code.append("begin")
        for line in self.impl:
            code.append(f"    {line}")
        code.append(f"end architecture {self.name}")
        return code


class DesignBuilder:
    def __init__(self) -> None:
        self.packages: list[VHDLPackage] = [IEEE.STD_LOGIC_1164,
                                            IEEE.STD_LOGIC_UNSIGNED]
        STD_LOGIC = Type("std_logic")
        self.entity: Entity = Entity(
            name="entity",
            port=Port(
                signals=[
                    Signal("clk", direction=Direction.IN, type=STD_LOGIC)
                ]
            )
        )
        self.architecture: Architecture = Architecture(name="rtl", entity_name="entity",
                                                       decl=[],
                                                       impl=[])

    def _build_library_section(self) -> list[str]:
        packages_by_library: dict[str, list[VHDLPackage]] = {}
        for package in self.packages:
            if package.library in packages_by_library:
                packages_by_library[package.library].append(package)
            else:
                packages_by_library[package.library] = []
        library_section = []
        for library in packages_by_library.keys():
            library_section.append(f"library {library}")
            for package in packages_by_library[library]:
                library_section.append(f"    use {library}.{package.name}.all;")
        return library_section

    def build(self) -> list[str]:
        return self._build_library_section() + self.entity.build_code() + self.architecture.build_code()


class _RomDirector:
    def __init__(self, name: str, addressing_strategy, data_type: VectorType, extra_packages: list[VHDLPackage], values) -> None:
        self._builder = DesignBuilder()
        std_logic = Type("std_logic")
        self._num_values = len(values)
        self._data_width = data_type.width
        self._address_signal: Signal[VectorType] = addressing_strategy.get_signal("addr", self._num_values)
        self._address_width = self._address_signal.type.width
        self._builder.entity = Entity(name=name,
                                      port=Port(signals=[
                                          Signal(name="clk",
                                                 direction=Direction.IN,
                                                 type=std_logic),
                                          Signal(name="en",
                                                 direction=Direction.IN,
                                                 type=std_logic),
                                          self._address_signal,
                                          Signal(name="data",
                                                 direction=Direction.OUT,
                                                 type=data_type)
                                      ]))
        self._builder.packages = [IEEE.STD_LOGIC_1164, IEEE.STD_LOGIC_UNSIGNED] + extra_packages
        self._values = [to_vhdl_binary_string(x, self._data_width) for x in
                        self._append_zeros_to_fill_addressable_memory(values)]
        self._resource_option = "auto"
        conversion = addressing_strategy.get_conversion_function()
        self._builder.architecture = Architecture("rtl", entity_name=name,
                                                  decl=[
                                                      f"type array_t is array (0 to "
                                                      f"2**{self._address_signal.type.width} - 1) "
                                                      f"of {data_type};",
                                                      f"signal ROM : array_t := ({','.join(self._values)});",
                                                      "attribute rom_style : string;",
                                                      f'attribute rom_style of ROM : signal is "{self._resource_option}";'
                                                  ],
                                                  impl=[
                                                      "ROM_process : process(clk)",
                                                      "begin",
                                                      "    if rising edge(clk) then",
                                                      "        if (en = '1') then",
                                                      f"            data <= ROM({conversion}(addr));",
                                                      "        end if;",
                                                      "    end if;",
                                                      "end process ROM_process;"
                                                  ])

    def build(self) -> list[str]:
        return self._builder.build()

    def _append_zeros_to_fill_addressable_memory(self, values: list[int]) -> list[int]:
        missing_number_of_zeros = 2 ** self._address_width - len(values)
        return values + _zeros(missing_number_of_zeros)


class StdLogicAddressing:
    def get_signal(self, name: str, num_values: int) -> Signal[VectorType]:
        width = calculate_address_width(num_values)
        return Signal(name, type=VectorType("std_logic_vector", width), direction=Direction.IN)

    def get_conversion_function(self) -> str:
        return "conv_integer"


class UnsignedAddressing:
    def get_signal(self, name: str, num_values: int) -> Signal[VectorType]:
        width = calculate_address_width(num_values)
        return Signal(name, type=VectorType("unsigned", width=width), direction=Direction.IN)

    def get_conversion_function(self) -> str:
        return "to_integer"


class Rom:
    def __init__(self, name: str, data_width: int, values_as_integers: list[int]) -> None:

        self._director = _RomDirector(name=name,
                                      data_type=VectorType("std_logic_vector", data_width),
                                      extra_packages=[],
                                      addressing_strategy=StdLogicAddressing(),
                                      values=values_as_integers
                                      )

    def save_to(self, destination: Path) -> None:
        template = SimpleTemplate(content=self._director.build(), parameters={})
        destination.as_file(".vhd").write(template)



class _Rom:
    def __init__(
        self, name: str, data_width: int, values_as_integers: list[int]
    ) -> None:
        self._name = name
        self._data_width = data_width
        number_of_values = len(values_as_integers)
        self._address_width = self._bits_required_to_address_n_values(number_of_values)
        self._values = [to_vhdl_binary_string(x, self._data_width) for x in
                        self._append_zeros_to_fill_addressable_memory(values_as_integers)]

    def save_to(self, destination: Path, std_logic_vector: bool = True):
        if std_logic_vector:
            file_name = "rom.tpl.bak.vhd"
        else:
            file_name = "rom_with_signed_values_unsigned_address.tpl.vhd"
        template = InProjectTemplate(
            file_name=file_name,
            package=module_to_package(self.__module__),
            parameters=dict(
                rom_value=self._rom_values(),
                rom_addr_bitwidth=str(self._address_width),
                rom_data_bitwidth=str(self._data_width),
                name=self._name,
                resource_option="auto",
            ),
        )
        destination.as_file(".vhd").write(template)

    def _rom_values(self) -> str:
        return ",".join(self._values)

    def _append_zeros_to_fill_addressable_memory(self, values: list[int]) -> list[int]:
        missing_number_of_zeros = 2**self._address_width - len(values)
        return values + _zeros(missing_number_of_zeros)

    def _bits_required_to_address_n_values(self, n: int) -> int:
        return calculate_address_width(n)


def _zeros(n: int) -> list[int]:
    return [0] * n


