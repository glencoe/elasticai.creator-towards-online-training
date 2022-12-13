from dataclasses import dataclass, field
from typing import Callable

from elasticai.creator.resource_utils import read_text
from vhdl.code_files.utils import (
    calculate_address_width,
    derive_fixed_point_params_from_factory,
)
from vhdl.code import Code
from elasticai.creator.vhdl.number_representations import FixedPoint
from vhdl.vhdl_files import expand_template


@dataclass
class LSTMFile:
    input_size: int
    hidden_size: int
    fixed_point_factory: Callable[[float], FixedPoint]
    work_library_name: str = field(default="work")

    def __post_init__(self) -> None:
        self.data_width, self.frac_width = derive_fixed_point_params_from_factory(
            self.fixed_point_factory
        )
        self.x_h_addr_width = calculate_address_width(
            self.input_size + self.hidden_size
        )
        self.hidden_addr_width = calculate_address_width(self.input_size)
        self.w_addr_width = calculate_address_width(
            (self.input_size + self.hidden_size) * self.hidden_size
        )

    @property
    def name(self) -> str:
        return "lstm.vhd"

    def __call__(self) -> Code:
        template = read_text("elasticai.creator.vhdl.templates", "lstm.tpl.vhd")

        code = expand_template(
            template,
            work_library_name=self.work_library_name,
            data_width=str(self.data_width),
            frac_width=str(self.frac_width),
            input_size=str(self.input_size),
            hidden_size=str(self.hidden_size),
            x_h_addr_width=str(self.x_h_addr_width),
            hidden_addr_width=str(self.hidden_addr_width),
            w_addr_width=str(self.w_addr_width),
        )

        yield from code
