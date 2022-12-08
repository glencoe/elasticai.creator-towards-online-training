from elasticai.creator.vhdl.modules.linear import FixedPointLinear as _FixedPointLinear
from vhdl.components.network_component import (
    SignalsForComponentWithBuffer,
    BufferedComponentInstantiation,
)
from vhdl.components.utils import calculate_address_width
from vhdl.code import Code


class FixedPointLinear(_FixedPointLinear):
    def signals(self, prefix) -> Code:
        signals = SignalsForComponentWithBuffer(
            name=prefix,
            data_width=self.fixed_point_factory.total_bits,
            x_address_width=calculate_address_width(self.in_features),
            y_address_width=calculate_address_width(self.out_features),
        )
        yield from signals

    def instantiation(self, prefix) -> Code:
        instantiation = BufferedComponentInstantiation(
            name=prefix,
        )
        yield from instantiation
