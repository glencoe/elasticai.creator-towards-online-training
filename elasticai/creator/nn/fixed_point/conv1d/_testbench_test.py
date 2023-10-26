import pytest

from .testbench import Conv1dTestbench
from ..number_converter import FXPParams


def construct_parameters():
    def combine_pairs_with_fxp_params(fxp_params, input_expected_pairs):
        return [(fxp_params, a, b) for a, b in input_expected_pairs]

    return combine_pairs_with_fxp_params(fxp_params=FXPParams(total_bits=3, frac_bits=0), input_expected_pairs=[
            ("010", [2.0]),
            ("001, 010", [1., 2.]),
            ("111, 001", [-1., 1.])
        ]) + combine_pairs_with_fxp_params(
        fxp_params=FXPParams(total_bits=4, frac_bits=1),
        input_expected_pairs=[("0001, 1111", [0.5, -0.5])]
    )


@pytest.mark.parametrize("fxp_params, reported, y", construct_parameters())
def test_parse_reported_content(fxp_params, reported, y):
    bench = Conv1dTestbench("conv1d_testbench", fxp_params)
    assert [y] == bench.parse_reported_content([reported])