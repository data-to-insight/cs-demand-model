import itertools
from datetime import date, timedelta

import numpy as np
import pandas as pd

from cs_demand_model.population_stats import PopulationStats

try:
    import tqdm
except ImportError:
    tqdm = None


def ageing_out(config):
    ageing_out = []
    for age_group in config.AgeBrackets:
        for pt in age_group.placement_categories:
            next_name = (age_group.next.name, pt.name) if age_group.next else tuple()
            ageing_out.append(
                {
                    "from": (age_group.name, pt.name),
                    "to": next_name,
                    "rate": age_group.daily_probability,
                }
            )

    df = pd.DataFrame(ageing_out)
    df.set_index(["from", "to"], inplace=True)
    return df.rate


def calculate_transfers_out(
    initial_population: pd.Series, transition_rates: pd.Series
) -> pd.DataFrame:
    """
    Calculate the number of people that will be transferred out of each placement type and age bin
    """
    # We start with the full population
    df_out = pd.DataFrame(initial_population)
    df_out.columns = ["initial"]
    df_out.index.names = ["from"]

    # Add the transition 'out' rates (so summed for the particular level)
    df_out["out_rate"] = transition_rates.groupby(level=0).sum()

    # Calculate the number of people that will be transferred out
    df_out["transfer_out"] = df_out.initial * df_out.out_rate

    # If at any point the transfers out exceed the population, we set the transfers out to the population
    df_out.loc[df_out.transfer_out > df_out.initial, "transfer_out"] = df_out.initial

    # Fill any NaNs with 0
    df_out = df_out.fillna(0)
    return df_out


def calculate_transfers_in(
    transfers_out: pd.DataFrame, transition_rates: pd.Series
) -> pd.DataFrame:
    """
    Calculate the number of people that will be transferred out of each placement type and age bin
    """
    # We start with all of the transitions
    df_in = pd.DataFrame(transition_rates)
    df_in.columns = ["transition_rates"]
    df_in.index.names = ["from", "to"]
    df_in.reset_index(level=1, inplace=True)

    # Add rates for the from groups
    df_in["group_rates"] = transfers_out.out_rate

    # Calculate fraction for each individual transition
    df_in["fraction"] = df_in.transition_rates / df_in.group_rates

    # Now insert the numbers that have been transferred out
    df_in["out"] = transfers_out.transfer_out

    # And calculate the transfer in numbers
    df_in["transfer_in"] = df_in.fraction * df_in.out

    # For transfers in, we always assume a ratio of 1 days
    df_in["transfer_in"] = np.where(
        df_in.index == tuple(), df_in.transition_rates, df_in.transfer_in
    )

    df_in.set_index(["to"], append=True, inplace=True)

    return df_in


def calculate_rate_from_numbers(
    initial_population: pd.Series, transition_numbers: pd.Series
) -> pd.Series:
    df_num = pd.DataFrame(transition_numbers)
    df_num.columns = ["transition_numbers"]
    df_num.index.names = ["from", "to"]
    df_num.reset_index(level=1, inplace=True)
    df_num["population"] = initial_population

    # For transfers in, we always assume a population of 1
    df_num.loc[df_num.index.get_level_values(0) == tuple(), "population"] = 1
    df_num["rate"] = df_num.transition_numbers / df_num.population

    df_num.set_index(["to"], append=True, inplace=True)

    return df_num.rate


def transition_population(
    initial_population: pd.Series,
    transition_rates: pd.Series = None,
    transition_numbers: pd.Series = None,
    days: int = 1,
):
    assert days > 0, "Days must be greater than 0"
    if transition_rates is None and transition_numbers is None:
        return initial_population.copy()

    if transition_numbers is not None:
        # Calculate transition rates from transition numbers
        transition_numbers = calculate_rate_from_numbers(
            initial_population, transition_numbers
        )

    if days > 1:
        if transition_rates is not None:
            transition_rates = 1 - (1 - transition_rates) ** days
        if transition_numbers is not None:
            transition_numbers = transition_numbers * days

    if transition_numbers is not None and transition_rates is not None:
        # Combine rates
        transition_numbers, transition_rates = transition_numbers.align(
            transition_rates
        )
        transition_rates = transition_rates.fillna(0) + transition_numbers.fillna(0)
    elif transition_numbers is not None:
        transition_rates = transition_numbers

    df_out = calculate_transfers_out(initial_population, transition_rates)
    df_in = calculate_transfers_in(df_out, transition_rates)
    transfer_in = (
        df_in.transfer_in.groupby(level=["to"])
        .sum()
        .reindex(initial_population.index, fill_value=0)
    )

    to_transfer = initial_population - df_out.transfer_out + transfer_in

    return to_transfer


class ModelPredictor:
    def __init__(
        self,
        population: pd.Series,
        transition_rates: pd.Series,
        transition_numbers: pd.Series,
        start_date: date,
    ):
        self.__initial_population = population
        self.__transition_rates = transition_rates
        self.__transition_numbers = transition_numbers
        self.__start_date = start_date

    @property
    def transition_rates(self):
        return self.__transition_rates.copy()

    @property
    def transition_numbers(self):
        return self.__transition_numbers.copy()

    @staticmethod
    def from_model(model: PopulationStats, reference_start: date, reference_end: date):
        transition_rates = model.raw_transition_rates(reference_start, reference_end)
        transition_rates.index.names = ["from", "to"]

        daily_entrants = model.daily_entrants(reference_start, reference_end)
        daily_entrants.index.names = ["from", "to"]

        aged_out = ageing_out(model.config)
        transition_rates, aged_out = transition_rates.align(aged_out)
        transition_rates = transition_rates.fillna(0) + aged_out.fillna(0)
        transition_rates.index.names = ["from", "to"]

        return ModelPredictor(
            population=model.stock_at(reference_end),
            transition_rates=transition_rates,
            transition_numbers=daily_entrants,
            start_date=reference_end,
        )

    @property
    def initial_population(self):
        return self.__initial_population

    @property
    def date(self):
        return self.__start_date

    def next(self, step_days: int = 1):
        next_population = transition_population(
            self.initial_population,
            self.__transition_rates,
            self.__transition_numbers,
            days=step_days,
        )

        next_date = self.date + timedelta(days=step_days)
        next_population.name = next_date

        return ModelPredictor(
            next_population,
            self.__transition_rates,
            self.__transition_numbers,
            next_date,
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
