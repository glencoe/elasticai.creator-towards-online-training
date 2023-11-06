from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import Any, Generic, TypeVar


@dataclass(frozen=True)
class VHDLPackage:
    name: str
    library: str


class Library(Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
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
        return f"{self.name}({self.width}-1 downto 0)"


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
        code.append(f"end architecture {self.name};")
        return code
