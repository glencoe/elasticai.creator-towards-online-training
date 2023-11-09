from elasticai.creator.file_generation.savable import Path
from elasticai.creator.vhdl.auto_wire_protocols.port_definitions import create_null_port
from elasticai.creator.vhdl.design.design import Design
from elasticai.creator.vhdl.design.ports import Port


class NullDesign(Design):
    """Design that will not generate any files and will be skipped in the sequential,
    when handed to the autowiring mechanism.
    """

    @property
    def port(self) -> Port:
        return create_null_port()

    def save_to(self, destination: Path) -> None:
        pass
