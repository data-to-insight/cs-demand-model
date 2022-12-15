from datetime import date, timedelta

import pandas as pd

from cs_demand_model.population_stats import PopulationStats

try:
    import tqdm
except ImportError:
    tqdm = None


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
    df_in.loc[df_in.index.isnull(), "transfer_in"] = df_in.transition_rates

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
    df_num.loc[df_num.index.get_level_values(0).isnull(), "population"] = 1
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
        transition_rates = transition_rates + transition_numbers
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
        rates_matrix: pd.Series,
        entrants: pd.Series,
        start_date: date,
    ):
        self.__initial_population = population
        self.__rates_matrix = rates_matrix
        self.__entrants = entrants
        self.__start_date = start_date

    @staticmethod
    def from_model(model: PopulationStats, reference_start: date, reference_end: date):
        transition_rates = model.transition_rates(reference_start, reference_end)
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

    def transition_population(self, start_population: pd.Series, step_days: int = 1):
        """
        Shuffles the population according to the transition rates by one day
        """
        # Multiply the rates matrix by the current population
        rates_matrix = self.__rates_matrix
        rates_matrix = rates_matrix.unstack().fillna(0)

        adjusted = start_population
        for _ in range(step_days):
            adjusted = rates_matrix.multiply(adjusted, axis="index")

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
