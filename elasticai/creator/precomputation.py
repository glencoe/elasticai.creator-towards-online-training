import json
from typing import Union, Set, Callable

import numpy as np
import torch
from torch import Tensor
from torch.nn import Module

from elasticai.creator.tags_utils import has_tag, get_tags, tag

_precomputable_tag = 'precomputable'


class Precomputation:
    """
    The Precomputation class provides a higher level api for precomputing the results of arbitrary pytorch modules.
    It is not a pytorch module itself nor intended to be used like one.
    """

    def __init__(self, module: Module, input_domain: Union[Callable[[], Tensor], Tensor]) -> None:
        super().__init__()
        self.module = module
        self.input_domain = input_domain
        self.output = None

    def _evaluate_input_domain_if_necessary(self) -> None:
        if isinstance(self.input_domain, Callable):
            self.input_domain = self.input_domain()

    @staticmethod
    def from_precomputable_tagged(module: Module):
        if not has_tag(module, _precomputable_tag):
            raise TypeError
        info_for_precomputation = get_tags(module)[_precomputable_tag]
        input_domain = info_for_precomputation['input_generator']
        return Precomputation(module=module,
                              input_domain=input_domain)

    def __call__(self, *args, **kwargs) -> None:
        """Precompute the input output pairs for the block handed during construction of the object.

        IMPORTANT: We assume the model is in eval mode
        """
        with torch.no_grad():
            self._evaluate_input_domain_if_necessary()
            self.output = self.module(self.input_domain)

    def __getitem__(self, item) -> Tensor:
        if item == 0:
            return self.input_domain
        elif item == 1:
            return self.output
        else:
            raise IndexError

    def dump_to(self, f):
        description = ""
        description += self.module.extra_repr()
        if description == "":
            description = []
            for name, child in self.module.named_children():
                description.append(name + " " + type(child).__name__)
        json.dump({
            'description': description,
            'shape': get_tags(self.module)['precomputable']['input_shape'],
            'x': self.input_domain.numpy().tolist(),
            'y': self.input_domain.numpy().tolist()
        },
            f,
        )


def get_precomputations_from_direct_children(module):
    def tag_filter(child):
        return _precomputable_tag in get_tags(child)

    submodules = tuple(module.children())
    filtered_submodules = filter(tag_filter, submodules)
    yield from (Precomputation.from_precomputable_tagged(submodule)
                for submodule in filtered_submodules)


def precomputable(module: Module,
                  input_shape: tuple[int, ...],
                  input_generator: Callable[[tuple[int, ...]], np.ndarray]) -> Module:
    """Add all necessary information to allow later tools to precompute the specified module

    The arguments provided will be used to determine the input data that needs
    to be fed to the module to produce the precomputed input-output table.

            Example:

            model = Sequence(
                precomputable(Sequence(
                    QConv1D(...),
                    BatchNorm1D(...),
                    Binarize(),
                ), input_shape=..., input_generator=...),
                precomputable(Sequence(
                    QConv1D(...),
                    BatchNorm1D(...),
                    Binarize(),
                ), input_shape=..., input_generator=...),
                MaxPool1D(..),

            precomputations = get_precomputations(model)
            for precompute in precomputations:
                precompute()

            with open('saved_precomputations.txt', 'w') as file:
                for precomputation in precomputations:
                    file.write(precomputation)
    """
    return tag(module, precomputable={
        'input_shape': input_shape,
        'input_generator': input_generator,
    })