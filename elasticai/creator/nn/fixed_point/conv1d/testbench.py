from abc import abstractmethod
from typing import Protocol
from collections import defaultdict

from elasticai.creator.vhdl.design.ports import Port
from elasticai.creator.file_generation.savable import Path
from elasticai.creator.file_generation.template import (
    InProjectTemplate,
    module_to_package,
)

from elasticai.creator.nn.fixed_point.number_converter import NumberConverter, FXPParams
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
    @property
    @abstractmethod
    def in_channels(self) -> int:
        ...

    @property
    @abstractmethod
    def out_channels(self) -> int:
        ...


class Conv1dTestbench:
    def __init__(self, name: str, uut: Conv1dDesign, fxp_params: FXPParams):
        self._converter = NumberConverter(fxp_params)
        self._converter_for_batch = NumberConverter(FXPParams(8, 0))  # max for 255 lines of inputs
        self._name = name
        self._uut_name = uut.name
        self._input_signal_length = uut.input_signal_length
        self._in_channels = uut.in_channels
        self._out_channels = uut.out_channels
        self._x_address_width = uut.port["x_address"].width
        self._fxp_params = fxp_params
        self._converter = NumberConverter(self._fxp_params)
        self._kernel_size = uut.kernel_size
        self._output_signal_length = math.floor(
            self._input_signal_length - self._kernel_size + 1
        )
        self._y_address_width = uut.port["y_address"].width

    def save_to(self, destination: Path):
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name="testbench.tpl.vhd",
            parameters={
                "testbench_name": self.name,
                "input_signal_length": str(self._input_signal_length),
                "in_channels": str(self._in_channels),
                "out_channels": str(self._out_channels),
                "total_bits": str(self._fxp_params.total_bits),
                "x_address_width": str(self._x_address_width),
                "output_signal_length": str(self._output_signal_length),
                "y_address_width": str(self._y_address_width),
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
        results_dict = defaultdict(list)
        print()
        for line in map(str.strip, content):
            if line.startswith("result: "):
                batch_text = line.split(":")[1].split(",")[0][1:]
                output_text = line.split(":")[1].split(",")[1][0:]
                print("output_text: ", output_text)
                batch = int(self._converter_for_batch.bits_to_rational(batch_text))
                if "U" not in line.split(":")[1].split(",")[1][1:]:
                    output = self._converter.bits_to_rational(output_text)
                else:
                    output = output_text
                results_dict[batch].append(output)
            else:
                print(line)
        results = list()
        for x in results_dict.items():
            results.append(x[1])
        if len(results) is 0:
            raise Exception(content)
        return list(results)
