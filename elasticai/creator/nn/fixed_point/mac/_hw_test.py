from itertools import chain
from math import ceil, floor

import pytest
import torch

from elasticai.creator.vhdl.ghdl_simulation import GHDLSimulator

from ..number_converter import FXPParams
from .layer import MacLayer

integer_test_data = [
    (FXPParams(4, 0), x1, x2)
    for x1, x2 in [
        ((1.0, 0.0), (-1.0, 0.0)),
        ((1.0, 0.0), (0.0, 0.0)),
        ((1.0, 0.0), (3.0, 0.0)),
        ((2.0, 0.0), (4.0, 0.0)),
        ((-2.0, 0.0), (4.0, 0.0)),
        ((-8.0, -8.0), (7.0, 7.0)),
        ((1.0, 1.0), (1.0, 1.0)),
    ]
]

fractions_test_data = [
    (FXPParams(5, 2), x1, x2)
    for x1, x2 in [
        # 00010 * 00010 -> 00000 00100 -> 000(00 001)00 -> 00001
        ((0.5, 0.0), (0.5, 0.0)),
        # 00010 * 01000 -> 00000 10000 -> 000(00 100)00 -> 00100
        ((0.5, 0.0), (2.0, 0.0)),
        ((0.25, 0.0), (0.5, 0.0)),
        ((0.5, 0.5), (0.5, 0.5)),
        ((-0.25, -1.0), (0.5, 0.5)),
        ((0.25, 1.0), (0.5, 0.25)),
        # 00001 * 00010 + 00100 * 00001 -> 00000 00010 + 00000 00100 -> 00000 0110 -> 00(000 01)10 -> 00(000 10)00 -> 00010
        ((0.25, 1.0), (0.5, 0.25)),
        ((-0.25, -1.0), (0.5, 0.5)),
        ((-4.0, -4.0), (3.75, 3.75)),
        ((0.25, 1.0), (0.5, 0.25)),
        ((-0.25, -1.0), (0.5, 0.5)),
        ((-4., 0.), (1., 0.)),
        ((-4., -1.), (1., 1.)),
        ((1.5, -1.), (0.5, 2.)),
        ((3.75, 1.), (1., 1.))

    ]
]


@pytest.mark.simulation
@pytest.mark.parametrize(
    ["fxp_params", "x1", "x2"], integer_test_data + fractions_test_data
)
def test_mac_hw_for_integers(tmp_path, fxp_params, x1, x2):
    root_dir_path = str(tmp_path)
    mac = MacLayer(fxp_params=fxp_params, vector_width=2)
    y = mac(torch.tensor(x1), torch.tensor(x2)).item()
    sim = mac.create_simulation(GHDLSimulator, root_dir_path)
    actual = sim(x1, x2)
    assert y == actual


def reference_macop_in_native_python(
    a_v: list[float], b_v: list[float], total_bits: int, frac_bits: int
) -> float:
    max_int = 2 ** (total_bits - 1) - 1
    min_int = -1 * 2 ** (total_bits - 1)

    def clamp(x):
        return min(max_int, max(min_int, x))

    def round_towards_zero(x):
        if x < 0:
            return ceil(x)
        else:
            return floor(x)

    def to_int(x):
        return int(x * 2**frac_bits)

    int_a_v = list(map(to_int, a_v))
    int_b_v = list(map(to_int, b_v))
    for value in chain(int_a_v, int_b_v):
        if value > max_int or value < min_int:
            raise ValueError(f"value {value} needs to be clamped to ({min_int}, {max_int})!")
    ys = [a * b for a, b in zip(int_a_v, int_b_v)]
    y = sum(ys)
    y = y / (2**frac_bits)
    y = clamp(y)
    y = round_towards_zero(y)
    return y / (2**frac_bits)


@pytest.mark.parametrize(
    "x1, x2, expected",
    [
        ((0.25, 1.0), (0.5, 0.25), 0.25),
        ((-0.25, -1.0), (0.5, 0.5), -0.5),
        ((-4., -1.), (1., 1.), -4.),
        ((3.75, 1.), (1., 1.), 3.75)
    ],
)
def test_hw_modelling_macop_in_native_python(x1, x2, expected):
    total_bits = 5
    frac_bits = 2
    assert expected == reference_macop_in_native_python(x1, x2, total_bits, frac_bits)


def test_throw_error_for_inputs_out_of_range():
    x1 = (4., 0.)
    x2 = (1., 0.)
    with pytest.raises(ValueError):
        reference_macop_in_native_python(x1, x2, total_bits=5, frac_bits=2)


@pytest.mark.parametrize(
    "x1, x2",
    [
        # 00001 * 00010 + 00100 * 00001 -> 00000 00010 + 00000 00100 -> 00000 00110 -> 000(00 001)10 -> 00001
        ((0.25, 1.0), (0.5, 0.25)),
        # 11111 * 00010 + 11100 * 00010 -> 11111 11111 * 00000 00010 + 11111 11100 * 00000 00010
        #  ->  11111 11110
        #    + 11111 11000
        #   -> 11111 10110 -> 111(11 101)10 -> rounding up: 111(11 110)10 -> 11110
        ((-0.25, -1.0), (0.5, 0.5)),
    ],
)
def test_torch_layer_behaves_as_reference_impl(x1, x2):
    fxp_params = FXPParams(total_bits=5, frac_bits=2)
    expected = reference_macop_in_native_python(x1, x2, frac_bits=2, total_bits=5)
    mac = MacLayer(fxp_params=fxp_params, vector_width=len(x1))
    y = mac(torch.tensor(x1), torch.tensor(x2)).item()
    assert expected == y
