from typing import Any

from elasticai.creator.vhdl.simulated_layer import Testbench


class Conv1dTestbench(Testbench):

    @property
    def name(self) -> str:
        return "conv1d_testbench"

    def set_inputs(self, *inputs) -> None:
        pass

    def parse_reported_content(self, content: Any) -> Any:
        return 1