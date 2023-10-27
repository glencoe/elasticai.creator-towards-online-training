'''
1. create testbench
2. save testbench to build folder
3. hand sequence of vhdl files in correct order to simulation tool
4. hand input data for testcase to simulation tool
5. let simulation tool compile files (if necessary)
6. let simulation tool run the simulation
7. parse/deserialize simulation output to required data
'''
from typing import Any

import pytest
import torch
import csv

from creator.file_generation.on_disk_path import OnDiskPath
from creator.nn.fixed_point import Conv1d
from creator.nn.fixed_point.conv1d.testbench import Conv1dTestbench
from creator.vhdl.ghdl_simulation import GHDLSimulator


class SimulatedLayer:
    def __init__(self, testbench: Conv1dTestbench, simulator_constructor, working_dir):
        self._testbench = testbench
        self._simulator_constructor = simulator_constructor
        self._working_dir = working_dir

    def __call__(self, *inputs: torch.Tensor) -> Any:
        self._testbench.write_inputs_to_csv(self._working_dir, inputs)
        runner = self._simulator_constructor(
            workdir=f"{self._working_dir}", top_design_name=self._testbench.name
        )
        runner.initialize()
        runner.run()
        actual = self._testbench.parse_reported_content(runner.getReportedContent())
        return actual


@pytest.mark.parametrize("x", ([[1., 1., 1.]],
                               [[0., 1., 1.]]))
def test_verify_hw_sw_equivalence_3_inputs(x):
    input_data = torch.Tensor(x)
    sw_conv = Conv1d(total_bits=4,
                     frac_bits=1,
                     in_channels=1,
                     out_channels=1,
                     signal_length=3,
                     kernel_size=2,
                     bias=False)
    sw_conv.weight.data = torch.ones_like(sw_conv.weight)
    sw_output = sw_conv(input_data)
    uut_name = "conv1d"
    design = sw_conv.create_design(uut_name)
    testbench = sw_conv.create_testbench(uut_name)
    build_dir = OnDiskPath("build")
    design.save_to(build_dir.create_subpath("srcs"))
    testbench.save_to(build_dir.create_subpath("testbenches"))
    sim_layer = SimulatedLayer(testbench, GHDLSimulator, working_dir="build")
    sim_output = sim_layer(input_data)
    assert sw_output.tolist() == sim_output

@pytest.mark.parametrize("x", ([[1., 1., 1., 1.]],
                               [[0., 1., 1., 0.]]))
def test_verify_hw_sw_equivalence_4_inputs(x):
    input_data = torch.Tensor(x)
    sw_conv = Conv1d(total_bits=4,
                     frac_bits=1,
                     in_channels=1,
                     out_channels=1,
                     signal_length=4,
                     kernel_size=2,
                     bias=False)
    sw_conv.weight.data = torch.ones_like(sw_conv.weight)
    sw_output = sw_conv(input_data)
    uut_name = "conv1d"
    design = sw_conv.create_design(uut_name)
    testbench = sw_conv.create_testbench(uut_name)
    build_dir = OnDiskPath("build")
    design.save_to(build_dir.create_subpath("srcs"))
    testbench.save_to(build_dir.create_subpath("testbenches"))
    sim_layer = SimulatedLayer(testbench, GHDLSimulator, working_dir="build")
    sim_output = sim_layer(input_data)
    assert sw_output.tolist() == sim_output