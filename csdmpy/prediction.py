from datetime import date, timedelta
from typing import Optional

import pandas as pd

from csdmpy.indexer import TransitionIndexes
from csdmpy.population_stats import PopulationStats


class ModelFactory:
    def __init__(
        self, model: PopulationStats, reference_start: date, reference_end: date
    ):
        self.__model = model
        self.__reference_start = reference_start
        self.__reference_end = reference_end

    def predictor(self, start_date: date) -> "ModelPredictor":
        return ModelPredictor(self, start_date)

    @property
    def model(self) -> PopulationStats:
        return self.__model

    @property
    def transition_rates(self) -> pd.DataFrame:
        return self.__model.transition_rates(
            self.__reference_start, self.__reference_end
        )

    @property
    def entrants(self) -> pd.DataFrame:
        return self.__model.daily_entrants(self.__reference_start, self.__reference_end)


class ModelPredictor:
    def __init__(self, factory: ModelFactory, start_date: date):
        self.__factory = factory
        self.__start_date = start_date

        # Make sure we have a full set of populations
        self.__initial_population = factory.model.stock.loc[[self.__start_date]].copy(
            deep=False
        )
        self.__initial_population = self.__initial_population.T.reindex(
            TransitionIndexes.transitions_all(levels=2)
        ).fillna(0)

        self.__current_predictions = pd.DataFrame(
            columns=TransitionIndexes.transitions_all(levels=2)
        )

    @property
    def start_population(self):
        return self.__initial_population

    @property
    def predictions(self):
        return self.__current_predictions.copy(deep=False)

    @property
    def current(self):
        if self.__current_predictions.empty:
            return self.__initial_population
        else:
            return self.__current_predictions.iloc[-1]

    @property
    def aged_out(self):
        current = self.current.copy(deep=False)
        stock_column = current.columns[0]
        current = current.reset_index()
        current["prob"] = current.age_bin.apply(lambda x: x.daily_probability)
        current["aged_out"] = current.prob * current[stock_column]
        current["next_age_bin"] = current.age_bin.apply(lambda x: x.next)
        return current

    def temp_age_population(self, start_population: Optional[pd.DataFrame] = None):
        if start_population is None:
            c = self.current.copy(deep=False).iloc[:, 0]
        else:
            c = start_population.copy(deep=False)

        c = pd.DataFrame(c)

        aged_out = self.aged_out

        # Calculate those who age out per bin
        leaving = aged_out.set_index(["age_bin", "placement_type"]).aged_out

        # Calculate those who arrive per bin
        arriving = (
            aged_out.dropna().set_index(["next_age_bin", "placement_type"]).aged_out
        )
        arriving.index.names = ["age_bin", "placement_type"]

        # Add as columns and fill missing values with zero
        c["aged_out"] = leaving
        c["aged_in"] = arriving
        c = c.fillna(0)

        # Add the corrections
        c["adjusted"] = c.iloc[:, 0] - c.aged_out + c.aged_in
        return c

    def temp_transition_population(
        self, start_population: Optional[pd.DataFrame] = None
    ):
        if start_population is None:
            c = self.current.copy(deep=False).iloc[:, 0]
        else:
            c = start_population.copy(deep=False)

        # Create the to-from transition matrix
        rates_matrix = self.__factory.transition_rates.unstack().fillna(0)

        # Multiply the rates matrix by the current population
        adjusted = rates_matrix.multiply(c, axis="index")

        # Sum the rows to get the total number of transitions
        adjusted = adjusted.reset_index().groupby("age_bin").sum().stack()
        adjusted.index.names = ["age_bin", "placement_type"]
        adjusted.name = "population"

        return adjusted

    def temp_new_entrants(self, start_population: Optional[pd.DataFrame] = None):
        if start_population is None:
            c = self.current.copy(deep=False).iloc[:, 0]
        else:
            c = start_population.copy(deep=False)

        c = pd.DataFrame(c)
        c["entry_prob"] = self.__factory.entrants.daily_entry_probability
        c = c.fillna(0)

        return c.sum(axis=1)

    def predict(self, days: int = 1, progress=False):
        current_populations = self.current.copy(deep=False).iloc[:, 0]

        if progress:
            from tqdm import trange

            iterator = trange(days)
        else:
            iterator = range(days)

        predictions = []
        for i in iterator:
            current_populations = self.temp_age_population(current_populations)
            current_populations = self.temp_transition_population(
                current_populations.adjusted
            )
            current_populations = self.temp_new_entrants(current_populations)
            current_populations.name = self.__start_date + timedelta(days=i + 1)
            predictions.append(current_populations)

        return pd.concat(predictions, axis=1).T
