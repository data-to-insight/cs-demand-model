from datetime import date, timedelta

import pandas as pd

from cs_demand_model.population_stats import PopulationStats

try:
    import tqdm
except ImportError:
    tqdm = None


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

    @staticmethod
    def from_model(model: PopulationStats, reference_start: date, reference_end: date):
        transition_rates = model.raw_transition_rates(reference_start, reference_end)
        return ModelPredictor(
            model.stock_at(reference_end),
            transition_rates,
            model.daily_entrants(reference_start, reference_end),
            reference_end,
        )

    @property
    def initial_population(self):
        return self.__initial_population

    @property
    def date(self):
        return self.__start_date

    @property
    def rates(self):
        return self.__rates_matrix.copy()

    def aged_out(self, start_population: pd.Series, step_days: int = 1):
        current = start_population.reset_index()
        current["prob"] = current.age_bin.apply(
            lambda x: x.daily_probability * step_days
        )
        current["aged_out"] = current.prob * current[self.initial_population.name]
        current["next_age_bin"] = current.age_bin.apply(lambda x: x.next)
        return current

    def age_population(self, start_population: pd.Series, step_days: int = 1):
        """
        Ages the given population by one day and returns the
        """
        c = pd.DataFrame(start_population)

        aged_out = self.aged_out(start_population, step_days=step_days)

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

    def _remain_rates(self, rates):
        # Exclude self transitions
        exclude_self_transitions = [i for i in rates.index if i[1] != i[2]]
        rates = rates[exclude_self_transitions]

        # Now sum the remaining rates
        summed = rates.reset_index().groupby(["age_bin", "placement_type"]).sum()

        # Calculate the residual rate that should be the 'remain' rate
        summed["residual"] = 1 - summed.transition_rate

        # Transfer these to the 'self' category
        summed = summed.reset_index()
        summed["placement_type_after"] = summed.placement_type

        # Add index back
        summed = summed.set_index(["age_bin", "placement_type", "placement_type_after"])

        return summed.residual

    def transition_population(self, start_population: pd.Series, step_days: int = 1):
        """
        Shuffles the population according to the transition rates by one day
        """
        # Multiply the rates matrix by the current population
        rates_matrix = self.__rates_matrix * step_days
        rates_matrix = self._remain_rates(rates_matrix)
        rates_matrix = rates_matrix.unstack().fillna(0)

        adjusted = rates_matrix.multiply(start_population, axis="index")

        # Sum the rows to get the total number of transitions
        adjusted = adjusted.reset_index().groupby("age_bin").sum().stack()
        adjusted.index.names = ["age_bin", "placement_type"]
        adjusted.name = "population"

        return adjusted

    def add_new_entrants(self, start_population: pd.Series, step_days: int = 1):
        """
        Adds new entrants to the population
        """
        c = pd.DataFrame(start_population)
        c["entry_prob"] = self.__entrants * step_days
        c = c.fillna(0)

        return c.sum(axis=1)

    def next(self, step_days: int = 1):
        next_population = self.initial_population
        next_population = self.age_population(next_population, step_days=step_days)
        next_population = self.transition_population(
            next_population, step_days=step_days
        )
        next_population = self.add_new_entrants(next_population, step_days=step_days)

        next_date = self.date + timedelta(days=step_days)
        next_population.name = next_date

        return ModelPredictor(
            next_population, self.__rates_matrix, self.__entrants, next_date
        )

    def predict(self, steps: int = 1, step_days: int = 1, progress=False):
        predictor = self

        if progress and tqdm:
            iterator = tqdm.trange(steps)
            set_description = iterator.set_description
        else:
            iterator = range(steps)
            set_description = lambda x: None

        predictions = []
        for i in iterator:
            predictor = predictor.next(step_days=step_days)

            pop = predictor.initial_population
            pop.name = self.__start_date + timedelta(days=(i + 1) * step_days)
            predictions.append(pop)

            set_description(f"{pop.name:%Y-%m}")

        return pd.concat(predictions, axis=1).T
