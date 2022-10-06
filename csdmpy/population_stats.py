from functools import lru_cache, cached_property
from typing import Dict, Iterable

import pandas as pd
import numpy as np
from datetime import date

from csdmpy.constants import AgeBracket, PlacementCategory


def _group_and_count_dates(df: pd.DataFrame, column: str, name: str, age_name: str) -> pd.Series:
    """
    Group the DataFrame by the given column and count the number of rows in each group.
    """
    groups = df.groupby([column, "placement_type", age_name]).size()
    groups.name = name
    groups.index.names = ["date", "placement_type", 'age_bin']
    return groups


def transitions_all(exclude_self=False, levels=3):
    for age_bin in AgeBracket:
        for pt1 in age_bin.placement_categories:
            if levels == 2:
                yield age_bin, pt1
            else:
                for pt2 in age_bin.placement_categories:
                    if not (exclude_self and pt1 == pt2):
                        yield age_bin, pt1, pt2


def transitions_self():
    for age_bin in AgeBracket:
        for pt1 in age_bin.placement_categories:
            yield age_bin, pt1, pt1


def mix(source):
    source = list(source)
    if len(source[0]) == 2:
        names = ['age_bin', 'placement_type']
    else:
        names = ['age_bin', 'placement_type', 'placement_type_after']
    return pd.MultiIndex.from_tuples(source, names=names)


class PopulationStats:

    def __init__(self, df: pd.DataFrame):
        self.__df = df

    @property
    def df(self):
        return self.__df

    @lru_cache(maxsize=5)
    def get_daily_pops(self, start_date: date, end_date: date):
        """
        Calculates the daily population for each age bin and placement type by
        finding all the transitions (start or end of episode), summing to get total populations for each
        day and then resampling to get the daily populations.
        """
        beginnings = _group_and_count_dates(self.df, "DECOM", "nof_decoms", "age_bin")
        endings = _group_and_count_dates(self.df, "DEC", "nof_decs", "age_bin")

        pops = pd.merge(
            left=beginnings, right=endings, left_index=True, right_index=True, how="outer"
        )
        pops = pops.fillna(0).sort_values("date")

        transitions = pops["nof_decoms"] - pops["nof_decs"]

        total_counts = (
            transitions.groupby(["placement_type", "age_bin"])
                .cumsum()
                .unstack(["age_bin", "placement_type"])
        )

        daily_counts = total_counts.resample("D").first().fillna(method="ffill")

        return daily_counts.truncate(before=start_date, after=end_date).fillna(0)

    @cached_property
    def deltas(self):
        beginnings = self.df[['DECOM', 'age_bin', 'placement_type']].copy(deep=False)
        beginnings['state'] = list(zip(beginnings.age_bin, beginnings.placement_type))
        beginnings['delta'] = 1
        beginnings = beginnings[['DECOM', 'state', 'delta']]
        beginnings.columns = ['date', 'state', 'delta']

        endings = self.df[['DEC', 'age_bin', 'placement_type', 'placement_type_after']].copy(deep=False)
        endings['state'] = list(zip(endings.age_bin, endings.placement_type))
        endings['state_after'] = list(zip(endings.age_bin, endings.placement_type_after))
        endings['delta'] = -1
        endings = endings[['DEC', 'state', 'state_after', 'delta']]
        endings.columns = ['date', 'state', 'state_after', 'delta']

        return pd.concat([beginnings, endings])

    @property
    def stock(self):
        """
        Calculates the daily transitions for each age bin and placement type by
        finding all the transitions (start or end of episode), summing to get total populations for each
        day and then resampling to get the daily populations.
        """
        endings = self.df.groupby(['DEC', 'placement_type', 'age_bin']).size()
        endings.name = 'nof_decs'

        beginnings = self.df.groupby(['DECOM', 'placement_type', 'age_bin']).size()
        beginnings.name = 'nof_decoms'

        endings.index.names = ['date', 'placement_type', 'age_bin']
        beginnings.index.names = ['date', 'placement_type', 'age_bin']

        pops = pd.merge(left=beginnings, right=endings,
                        left_index=True, right_index=True, how='outer')

        pops = pops.fillna(0).sort_values('date')

        pops = (pops['nof_decoms'] - pops['nof_decs']).groupby(['placement_type', 'age_bin']).cumsum()

        pops = pops.unstack(['age_bin', 'placement_type']).resample('D').first().fillna(method='ffill').fillna(0)
        return pops

    @property
    def transitions(self):
        transitions = self.df.groupby(['placement_type', 'placement_type_after', 'age_bin', 'DEC']).size()
        transitions = transitions.unstack(level=['age_bin', 'placement_type', 'placement_type_after']).fillna(0).asfreq('D', fill_value=0)
        return transitions

    @lru_cache(maxsize=5)
    def raw_transition_rates(self, start_date: date, end_date: date):
        # Ensure we can calculate the transition rates by aligning the dataframes
        stock = self.stock.truncate(before=start_date, after=end_date)
        transitions = self.transitions.truncate(before=start_date, after=end_date)

        # Calculate the transition rates
        stock, transitions = stock.align(transitions)
        transition_rates = transitions / stock.shift(1).fillna(method='bfill')

        # Use the mean rates
        transition_rates = transition_rates.mean(axis=0)
        transition_rates.name = 'transition_rate'
        transition_rates = pd.DataFrame(transition_rates)

        # Fill in blank 'valid' values
        zeros = pd.DataFrame(0, index=mix(transitions_all(exclude_self=True)), columns=['zeros'])
        transition_rates = transition_rates.merge(zeros, left_index=True, right_index=True, how='outer').fillna(0)

        return transition_rates.transition_rate

    @lru_cache(maxsize=5)
    def summed_rates(self, start_date: date, end_date: date):
        rates = self.raw_transition_rates(start_date, end_date)

        # Exclude self transitions
        rates = rates[~rates.index.isin(transitions_self())]

        # Now sum the remaining rates
        rates = rates.reset_index().groupby(['age_bin', 'placement_type']).sum()
        return rates.transition_rate

    @lru_cache(maxsize=5)
    def remain_rates(self, start_date: date, end_date: date):
        summed = pd.DataFrame(self.summed_rates(start_date, end_date))

        # Calculate the residual rate that should be the 'remain' rate
        summed['residual'] = 1 - summed.transition_rate

        # Transfer these to the 'self' category
        summed = summed.reset_index()
        summed['placement_type_after'] = summed.placement_type

        # Add index back
        summed = summed.set_index(['age_bin', 'placement_type', 'placement_type_after'])

        return summed.residual

    @lru_cache(maxsize=5)
    def transition_rates(self, start_date: date, end_date: date, include_not_in_care=False):
        """
        The transition rates are the rates of transitions between placement types for each age bin. They include
        the calculated rates, as well as the 'remain' rate which is the rate of remaining in the same placement,
        not including those who leave the system.
        """
        transition_rates = self.raw_transition_rates(start_date, end_date)
        remain_rates = self.remain_rates(start_date, end_date)

        merged_rates = pd.concat([transition_rates, remain_rates], axis=1)

        merged_rates['merged'] = np.where(merged_rates.residual.isnull(), merged_rates.transition_rate, merged_rates.residual)

        merged_rates = merged_rates.merged
        merged_rates.name = "transition_rate"

        if not include_not_in_care:
            merged_rates = merged_rates.loc[mix(transitions_all())]

        return merged_rates

    @lru_cache(maxsize=5)
    def get_transitions(self, start_date: date, end_date: date):
        """
        Returns a DataFrame of transitions for each age bracket. The transitions are calculated from each
        episode end, using the placement type and the placement type after the episode end.

        """
        # We don't care about internal transitions
        df = self.df
        df = df[df.placement_type != df.placement_type_after]
        df = df[(df.DEC >= start_date) & (df.DEC <= end_date)]

        transitions = df.groupby(
            ["end_age_bin", "placement_type", "placement_type_after"]
        ).size()
        transitions.name = "transition_count"

        transitions = pd.DataFrame(transitions)
        transitions['period_duration'] = (end_date - start_date).days

        transitions['transition_probability'] = transitions.transition_count / transitions.period_duration
        transitions.index.names = ["age_bin", "placement_type", "placement_type_after"]
        return transitions

    @lru_cache(maxsize=5)
    def get_daily_entrants(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Returns the number of entrants and the daily_probability of entrants for each age bracket and placement type.
        """
        df = self.df

        # Only look at episodes starting in analysis period
        df = df[(df["DECOM"] >= start_date) & (df["DECOM"] <= end_date)]

        # Group by age bin and placement type
        df = df[df["placement_type_before"] == PlacementCategory.NOT_IN_CARE].groupby(["age_bin", "placement_type"]).size()
        df.name = 'entrants'

        # Reset index
        df = df.reset_index()

        df["period_duration"] = (end_date - start_date).days
        df['daily_entry_probability'] = df['entrants'] / df['period_duration']

        df = df.set_index(['age_bin', 'placement_type'])

        return df

    @cached_property
    def ageing_probs(self):
        daily_probs = [(*t, t[0].daily_probability) for t in transitions_all(levels=2)]
        daily_probs = pd.DataFrame(daily_probs, columns=['age_bin', 'placement_type', 'ageing_out'])
        daily_probs = daily_probs.set_index(['age_bin', 'placement_type'])
        return daily_probs.ageing_out
