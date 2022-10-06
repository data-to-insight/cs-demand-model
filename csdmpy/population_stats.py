from functools import lru_cache
import pandas as pd
import numpy as np
from datetime import date

from csdmpy.constants import PlacementCategory
from csdmpy.indexer import TransitionIndexes, TransitionLevels


class PopulationStats:

    def __init__(self, df: pd.DataFrame):
        self.__df = df

    @property
    def df(self):
        return self.__df

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
        zeros = pd.DataFrame(0, index=TransitionIndexes.transitions_all(exclude_self=True), columns=['zeros'])
        transition_rates = transition_rates.merge(zeros, left_index=True, right_index=True, how='outer').fillna(0)

        return transition_rates.transition_rate

    @lru_cache(maxsize=5)
    def summed_rates(self, start_date: date, end_date: date):
        rates = self.raw_transition_rates(start_date, end_date)

        # Exclude self transitions
        rates = rates[~rates.index.isin(TransitionLevels.transitions_self())]

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
            merged_rates = merged_rates.loc[TransitionIndexes.transitions_all()]

        return merged_rates

    @lru_cache(maxsize=5)
    def daily_entrants(self, start_date: date, end_date: date) -> pd.DataFrame:
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
