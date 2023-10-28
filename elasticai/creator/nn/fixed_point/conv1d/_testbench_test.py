from typing import Callable, Any

import pytest
import torch

from elasticai.creator.vhdl.auto_wire_protocols.port_definitions import create_port
from elasticai.creator.vhdl.design.ports import Port
from .testbench import Conv1dTestbench, Conv1dDesign
from ..number_converter import FXPParams


class DummyConv1d:
    def __init__(self, fxp_params: FXPParams):
        self.name: str = "conv1d"
        self.kernel_size: int = 1
        self.input_signal_length = 1
        self.port: Port = create_port(
            y_width=fxp_params.total_bits,
            x_width=fxp_params.total_bits,
            x_count=1,
            y_count=2,
        )


def parameters_for_reported_content_parsing():
    def add_expected_prefix_to_pairs(pairs):
        return [(f"result: {content}", number) for content, number in pairs]

    def combine_pairs_with_fxp_params(fxp_params, input_expected_pairs):
        return [
            (fxp_params, a, b)
            for a, b in add_expected_prefix_to_pairs(input_expected_pairs)
        ]

    return combine_pairs_with_fxp_params(
        fxp_params=FXPParams(total_bits=3, frac_bits=0),
        input_expected_pairs=[
            ("010", [2.0]),
            ("001, 010", [1.0, 2.0]),
            ("111, 001", [-1.0, 1.0]),
        ],
    ) + combine_pairs_with_fxp_params(
        fxp_params=FXPParams(total_bits=4, frac_bits=1),
        input_expected_pairs=[("0001, 1111", [0.5, -0.5])],
    )


@pytest.fixture
def create_uut() -> Callable[[Any], Conv1dDesign]:
    def create(fxp_params) -> Conv1dDesign:
        return DummyConv1d(fxp_params)

    return create


@pytest.mark.parametrize(
    "fxp_params, reported, y", parameters_for_reported_content_parsing()
)
def test_parse_reported_content(fxp_params, reported, y, create_uut):
    bench = Conv1dTestbench(
        name="conv1d_testbench", fxp_params=fxp_params, uut=create_uut(fxp_params)
    )
    assert [y] == bench.parse_reported_content([reported])


def test_input_preparation(create_uut):
    fxp_params = FXPParams(total_bits=3, frac_bits=0)
    bench = Conv1dTestbench(
        name="bench_name", fxp_params=fxp_params, uut=create_uut(fxp_params)
    )
    input = torch.Tensor([[[1.0, 1.0]]])
    expected = [{"x_0_0": "001", "x_0_1": "001"}]
    assert expected == bench.prepare_inputs(input.tolist())
