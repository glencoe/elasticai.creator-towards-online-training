from abc import abstractmethod
from typing import Protocol

from elasticai.creator.vhdl.design.ports import Port
from elasticai.creator.file_generation.savable import Path
from elasticai.creator.file_generation.template import (
    InProjectTemplate,
    module_to_package,
)
from ..number_converter import NumberConverter, FXPParams
import math


class Conv1dDesign(Protocol):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def input_signal_length(self) -> int:
        ...

    @property
    @abstractmethod
    def port(self) -> Port:
        ...

    @property
    @abstractmethod
    def kernel_size(self) -> int:
        ...


class Conv1dTestbench:
    def __init__(self, name: str, uut: Conv1dDesign, fxp_params: FXPParams):
        self._converter = NumberConverter(fxp_params)
        self._name = name
        self._uut_name = uut.name
        self._input_signal_length = uut.input_signal_length
        self._fxp_params = fxp_params
        self._converter = NumberConverter(self._fxp_params)
        self._kernel_size = uut.kernel_size
        self._output_signal_length = math.floor(
            self._input_signal_length - self._kernel_size + 1
        )

    def save_to(self, destination: Path):
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name="testbench.tpl.vhd",
            parameters={
                "testbench_name": self.name,
                "signal_length": str(self._input_signal_length),
                "total_bits": str(self._fxp_params.total_bits),
                "x_address_width": str(math.ceil(math.log2(self._input_signal_length))),
                "y_address_width": str(
                    math.ceil(math.log2(self._output_signal_length))
                ),
                "uut_name": self._uut_name,
            },
        )
        destination.create_subpath(self.name).as_file(".vhd").write(template)

    @property
    def name(self) -> str:
        return self._name

    def prepare_inputs(self, *inputs) -> list[dict]:
        batches = inputs[0]
        prepared_inputs = []
        for batch in batches:
            prepared_inputs.append({})
            for channel_id, channel in enumerate(batch):
                for time_step_id, time_step_val in enumerate(channel):
                    prepared_inputs[-1][f"x_{channel_id}_{time_step_id}"] = (
                        self._converter.rational_to_bits(time_step_val)
                    )

        return prepared_inputs

    def parse_reported_content(self, content: list[str]) -> list[list[float]]:
        result = list()
        print("content: ", content)
        for line in map(str.strip, content):
            print("line: ", line)
            if line.startswith("result: "):
                result.append(line.split(":")[1])
        if len(result) is 0:
            raise Exception(content)
        out_channel_content = result
        out_channel_content = [
            self._converter.bits_to_rational(y) for y in out_channel_content
        ]
        return [out_channel_content]
