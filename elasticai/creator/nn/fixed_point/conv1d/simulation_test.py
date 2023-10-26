'''
1. create testbench
2. save testbench to build folder
3. hand sequence of vhdl files in correct order to simulation tool
4. hand input data for testcase to simulation tool
5. let simulation tool compile files (if necessary)
6. let simulation tool run the simulation
7. parse/deserialize simulation output to required data
'''
import csv
from typing import Any

import pytest
import torch

from creator.file_generation.on_disk_path import OnDiskPath
from creator.nn.fixed_point import Conv1d
from creator.vhdl.ghdl_simulation import GHDLSimulator


class SimulatedLayer:
    def __init__(self, testbench, simulator_constructor, working_dir):
        self._testbench = testbench
        self._simulator_constructor = simulator_constructor
        self._working_dir = working_dir

    def __call__(self, **inputs) -> Any:
        runner = self._simulator_constructor(
            workdir=f"{self._working_dir}", top_design_name=self._testbench.name
        )
        with open(f"{self._working_dir}/{self._testbench.name}_inputs.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=inputs.keys())
            writer.writerows(inputs)
        runner.initialize()
        runner.run()
        actual = self._testbench.parse_reported_content(runner.getReportedContent())
        return actual


@pytest.mark.simulation
@pytest.mark.parametrize("x", ([[1., 1., 1.]],
                               [[0., 1., 1.]]))
def test_verify_hw_sw_equivalence(x):
    input_data = torch.Tensor(x)
    sw_conv = Conv1d(total_bits=3,
                     frac_bits=0,
                     in_channels=1,
                     out_channels=1,
                     signal_length=3,
                     kernel_size=2,
                     bias=False)
    sw_conv.weight.data = torch.ones_like(sw_conv.weight)
    sw_output = sw_conv(input_data)
    design = sw_conv.create_design("conv1d")
    testbench = sw_conv.create_testbench("conv1d_testbench")
    build_dir = OnDiskPath("build")
    design.save_to(build_dir.create_subpath("srcs"))
    testbench.save_to(build_dir.create_subpath("testbenches"))
    sim_layer = SimulatedLayer(testbench, GHDLSimulator, working_dir="build")
    sim_output = sim_layer(input_data)
    assert sw_output.tolist() == sim_output

