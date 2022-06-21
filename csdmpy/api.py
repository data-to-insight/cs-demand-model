from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping, Any

from csdmpy.classy import Model
from csdmpy.ingress import the_ingress_procedure
from csdmpy.utils import cost_translation
from csdmpy.config import cost_params_map


class ApiSession:
    def __init__(self, input_files: Iterable[Mapping[str, Any]]):
        self.df = the_ingress_procedure(input_files)
        self._model = None

    def calculate_model(self, model_params, adjustments):
        self._model = Model(self.df, model_params=model_params, adjustments=adjustments)

    def calculate_costs(self, costs, proportions, inflation=None):
        step_size = self._model.step_size
        nested_costs, nested_proportions = cost_translation(costs, proportions, cost_params_map)
        cost_params = {'cost_dict': nested_costs,
                       'proportions': nested_proportions,
                       'inflation': inflation,
                       'step_size': step_size}
        self._model.calculate_costs(cost_params)

    @property
    def model(self):
        return self._model
