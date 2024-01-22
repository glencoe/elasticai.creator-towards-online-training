import torch

from elasticai.creator.vhdl.design_creator import DesignCreator
from elasticai.creator.vhdl.shared_designs.null_design import NullDesign


class Flatten(torch.nn.Flatten, DesignCreator):
    def create_design(self, name: str) -> NullDesign:
        return NullDesign(name)
