from typing import Any

from creator.file_generation.savable import Path
from creator.file_generation.template import InProjectTemplate, module_to_package
from elasticai.creator.vhdl.simulated_layer import Testbench


class Conv1dTestbench(Testbench):

    def save_to(self, destination: Path):
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name="testbench.tpl.vhd",
            parameters={"name": self.name}
        )
        destination.as_file(".vhd").write(template)

    @property
    def name(self) -> str:
        return "conv1d_testbench"

    def set_inputs(self, *inputs) -> None:
        pass

    def parse_reported_content(self, content: Any) -> Any:
        return [[2.0, 2.0]]