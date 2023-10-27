import math
import os
from typing import Any
import csv

import torch

from creator.file_generation.savable import Path
from creator.file_generation.template import InProjectTemplate, module_to_package
from creator.nn.fixed_point._two_complement_fixed_point_config import FixedPointConfig
from creator.nn.fixed_point.number_converter import NumberConverter, FXPParams
from elasticai.creator.vhdl.simulated_layer import Testbench



class Conv1dTestbench(Testbench):
    def __init__(self, uut_name: str, total_bits, frac_bits, signal_length, kernel_size):
        self._uut_name = uut_name
        self._input_signal_length = signal_length
        self._fxp_params = FXPParams(total_bits, frac_bits)
        self._converter = NumberConverter(self._fxp_params)
        self._kernel_size = kernel_size
        self._input_file_name = 'inputs.csv'
        self._output_signal_length = math.floor(
            self._input_signal_length - self._kernel_size + 1
        )

        Testbench.__init__(self)

    def save_to(self, destination: Path):
        self._destination = destination
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name="testbench.tpl.vhd",
            parameters={"testbench_name": self.name,
                        "signal_length": str(self._input_signal_length),
                        "total_bits": str(self._fxp_params.total_bits),
                        "input_file_name": self._input_file_name,
                        "x_address_width": str(math.ceil(math.log2(self._input_signal_length))),
                        "y_address_width": str(math.ceil(math.log2(self._output_signal_length))),
                        "uut_name": self._uut_name
                        }
        )
        destination.as_file(".vhd").write(template)

    @property
    def name(self) -> str:
        return "conv1d_testbench"

    def set_inputs(self, *inputs) -> None:
        ...

    def write_inputs_to_csv(self, destination: str, inputs: tuple[torch.Tensor]) -> None:
        with open(os.path.join(destination, self._input_file_name), 'w', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=' ',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            header = list()
            for i in range(self._input_signal_length):
                header.append(f"x{i}")
            filewriter.writerow(header)

            for batch in inputs:
                for batch_num, singe_inference in enumerate(batch):
                    row = list()
                    for value_num, value_rational in enumerate(singe_inference):
                        value_int = self._converter.rational_to_bits(float(value_rational))
                        row.append(value_int)
                    filewriter.writerow(row)


    def parse_reported_content(self, content: Any) -> Any:
        print(content)
        return self._converter.bits_to_rational(content[0])