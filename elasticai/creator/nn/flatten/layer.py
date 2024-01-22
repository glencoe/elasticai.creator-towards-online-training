import torch

from elasticai.creator.vhdl.shared_designs.null_design import NullDesign


class Flatten(torch.nn.Flatten):
    def create_design(self, name: str):
        return NullDesign(name)
