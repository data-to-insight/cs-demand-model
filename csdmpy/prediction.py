from datetime import date, timedelta
from functools import cached_property
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
        # Make sure we have a full set of populations
        pop = (
            self.model.stock.loc[[start_date]]
            .copy(deep=False)
            .T.reindex(TransitionIndexes.transitions_all(levels=2))
            .fillna(0)[start_date]
        )

        return ModelPredictor(
            pop,
            self.transition_matrix,
            self.entrants.daily_entry_probability,
            start_date,
        )

    @property
    def model(self) -> PopulationStats:
        return self.__model

    @cached_property
    def transition_rates(self) -> pd.DataFrame:
        return self.__model.transition_rates(
            self.__reference_start, self.__reference_end
        )

    @cached_property
    def transition_matrix(self) -> pd.DataFrame:
        return self.transition_rates.unstack().fillna(0)

    @cached_property
    def entrants(self) -> pd.DataFrame:
        return self.__model.daily_entrants(self.__reference_start, self.__reference_end)


class ModelPredictor:
    def __init__(
        self,
        population: pd.Series,
        rates_matrix: pd.DataFrame,
        entrants: pd.Series,
        start_date: date,
    ):
        self.__initial_population = population
        self.__rates_matrix = rates_matrix
        self.__entrants = entrants
        self.__start_date = start_date

    @property
    def initial_population(self):
        return self.__initial_population

    @property
    def date(self):
        return self.__start_date

    def aged_out(self, start_population: pd.Series):
        current = start_population.reset_index()
        current["prob"] = current.age_bin.apply(lambda x: x.daily_probability)
        current["aged_out"] = current.prob * current[self.initial_population.name]
        current["next_age_bin"] = current.age_bin.apply(lambda x: x.next)
        return current

    def age_population(self, start_population: pd.Series):
        """
        Ages the given population by one day and returns the
        """
        c = pd.DataFrame(start_population)

        aged_out = self.aged_out(start_population)

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
        return c.adjusted

    def transition_population(self, start_population: pd.Series):
        """
        Shuffles the population according to the transition rates by one day
        """
        # Multiply the rates matrix by the current population
        adjusted = self.__rates_matrix.multiply(start_population, axis="index")

        # Sum the rows to get the total number of transitions
        adjusted = adjusted.reset_index().groupby("age_bin").sum().stack()
        adjusted.index.names = ["age_bin", "placement_type"]
        adjusted.name = "population"

        return adjusted

    def add_new_entrants(self, start_population: pd.Series):
        """
        Adds new entrants to the population
        """
        c = pd.DataFrame(start_population)
        c["entry_prob"] = self.__entrants
        c = c.fillna(0)

        return c.sum(axis=1)

    def next(self):
        next_population = self.initial_population
        next_population = self.age_population(next_population)
        next_population = self.transition_population(next_population)
        next_population = self.add_new_entrants(next_population)

        next_date = self.date + timedelta(days=1)
        next_population.name = next_date

        return ModelPredictor(
            next_population, self.__rates_matrix, self.__entrants, next_date
        )

    def predict(self, days: int = 1, progress=False):
        predictor = self

        if progress:
            from tqdm import trange

            iterator = trange(days)
        else:
            iterator = range(days)

        predictions = []
        for i in iterator:
            predictor = predictor.next()

            pop = predictor.initial_population
            pop.name = self.__start_date + timedelta(days=i + 1)
            predictions.append(pop)

            if progress:
                iterator.set_description(f"{pop.name}")

        return pd.concat(predictions, axis=1).T
