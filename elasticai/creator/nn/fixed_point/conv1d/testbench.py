from typing import Any

from elasticai.creator.vhdl.simulated_layer import Testbench


class Conv1dTestbench(Testbench):
    def set_inputs(self, *inputs) -> None:
        pass

    def parse_reported_content(self, content: Any) -> Any:
        pass