from typing import Iterable, Mapping, Any

from csdmpy.classy import Model
from csdmpy.ingress import the_ingress_procedure


class ApiSession:

    def __init__(self, input_files: Iterable[Mapping[str, Any]]):
        self.df = the_ingress_procedure(input_files)
        self._model = None

    def calculate_model(self, model_params, adjustments):
        self._model = Model(self.df, model_params=model_params, adjustments=adjustments)

    def calculate_costs(self, cost_params):
        self._model.calculate_costs(cost_params)

    @property
    def model(self):
        return self._model
