from math import ceil
from typing import Any, Mapping

from .util import convert_date


class Dates:
    def __init__(self, dates: Mapping[str, Any]):
        self.reference_start = convert_date(dates["referenceStart"])
        self.reference_end = convert_date(dates["referenceEnd"])
        self.forecast_end = convert_date(dates["forecastEnd"])
        self.step_days = int(dates.get("step_days", 10))

    @property
    def steps(self):
        steps = (self.forecast_end - self.reference_end).days / self.step_days
        return ceil(steps)


class Costs:
    def __init__(self, costs: Mapping[str, Any]):
        self.costs = costs

    def __getitem__(self, key):
        return self.costs[key]
