from elasticai.creator.file_generation.in_memory_path import InMemoryPath, InMemoryFile
from elasticai.creator.file_generation.on_disk_path import OnDiskPath
from elasticai.creator.nn.sequential import Sequential
from elasticai.creator.nn.fixed_point.conv1d import Conv1d
from typing import cast

import pytest
from elasticai.creator.vhdl.design.design import Design
from elasticai.creator.file_generation.in_memory_path import InMemoryFile, InMemoryPath

@pytest.fixture
def seq_conv1d_design() -> Design:
    return Sequential(Conv1d(
        total_bits=16,
        frac_bits=8,
        in_channels=1,
        out_channels=2,
        kernel_size=3,
        signal_length=4,
    )).create_design("network")

def save_design(design: Design) -> dict[str, str]:
    destination = InMemoryPath("network", parent=None)
    design.save_to(destination)
    files = cast(list[InMemoryFile], list(destination.children.values()))
    return {file.name: "\n".join(file.text) for file in files}

def test_network_generation(seq_conv1d_design: Design):
    saved_files = save_design(seq_conv1d_design)
    expected_files = {"conv1d_0_w_rom.vhd", "conv1d_0_b_rom.vhd", "conv1d_0.vhd", "conv1d_0_fxp_MAC_RoundToZero.vhd", "fxp_mac.vhd"}
    actual_files = set(saved_files.keys())

    assert expected_files == actual_files

