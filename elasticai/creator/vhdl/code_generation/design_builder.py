from creator.vhdl.code_generation.language import (
    IEEE,
    Architecture,
    Direction,
    Entity,
    Port,
    Signal,
    Type,
    VHDLPackage,
)


class DesignBuilder:
    def __init__(self) -> None:
        """The initialization below are example fields.
        The director is responsible for setting these correctly."""
        self.packages: list[VHDLPackage] = [
            IEEE.STD_LOGIC_1164,
            IEEE.STD_LOGIC_UNSIGNED,
        ]
        STD_LOGIC = Type("std_logic")
        self.entity: Entity = Entity(
            name="entity",
            port=Port(signals=[Signal("clk", direction=Direction.IN, type=STD_LOGIC)]),
        )
        self.architecture: Architecture = Architecture(
            name="rtl", entity_name="entity", decl=[], impl=[]
        )

    def _build_library_section(self) -> list[str]:
        packages_by_library: dict[str, list[VHDLPackage]] = {}
        for package in self.packages:
            if package.library not in packages_by_library:
                packages_by_library[package.library] = []
            packages_by_library[package.library].append(package)
        library_section = []
        for library in packages_by_library.keys():
            library_section.append(f"library {library};")
            for package in packages_by_library[library]:
                library_section.append(f"    use {library}.{package.name}.all;")
        return library_section

    def build(self) -> list[str]:
        return (
            self._build_library_section()
            + self.entity.build_code()
            + self.architecture.build_code()
        )
