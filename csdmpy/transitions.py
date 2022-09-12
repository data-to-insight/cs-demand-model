from datetime import date
from typing import Dict

import numpy as np
import pandas as pd

from csdmpy.constants import AgeBracket
from csdmpy.populations import get_daily_pops_new_way


def get_transitions(df, start_date: date, end_date: date):
    """
    Returns a DataFrame of transitions for each age bracket. The transitions are calculated from each
    episode end, using the placement type and the placement type after the episode end.

    TODO: This uses the "placement_type_after" column of the standard view - but this could be calculated here to keep the logic in one place.
    """
    transitions = df.groupby(
        ["placement_type", "placement_type_after", "age_bin", "DEC"]
    )
    transitions = transitions.size().unstack(
        level=["age_bin", "placement_type", "placement_type_after"]
    )
    if start_date:
        transitions = transitions.truncate(before=start_date)
    if end_date:
        transitions = transitions.truncate(after=end_date)
    transitions = transitions.fillna(0).asfreq("D", fill_value=0)
    return transitions


def get_transition_rates(df: pd.DataFrame, start_date: date, end_date: date):
    """
    Returns a DataFrame of transition rates for each age bracket. The transition rates are based on the
    ratio between stock and flow - the number of transitions divided by the starting population.

    The rates are given based on age and placement type.

    :param df: The dataframe containing the data
    :param start_date: The start date of the window to calculate rates for
    :param end_date: The end date of the window to calculate rates for
    """
    populations = get_daily_pops_new_way(df, start_date, end_date)
    transitions = get_transitions(df, start_date, end_date)

    populations_aligned, transitions_aligned = populations.align(transitions)
    transition_rates = transitions_aligned / populations_aligned.shift(1).fillna(
        method="bfill"
    )
    transition_rates = (
        transition_rates.mean(axis=0).unstack(["age_bin", "placement_type"]).fillna(0)
    )
    return transition_rates


def group_transition_rates(
    transition_rates: pd.DataFrame,
) -> Dict[AgeBracket, pd.DataFrame]:
    """
    Takes a DataFrame of transition rates and groups them by age bracket. The DataFrame is expected to be in the
    format returned by `get_transition_rates()`.

    :param transition_rates: The DataFrame of transition rates
    :return: A mapping of age bracket to transition rates

    """
    bins_in_data = transition_rates.columns.get_level_values("age_bin").unique()
    transidict = {}
    for ab in AgeBracket:
        valid_places = ab.placement_categories
        if ab in bins_in_data:
            t_matrix = transition_rates[ab].copy()

            # set all transitions to zero that are not valid
            for pt in set(valid_places) - set(t_matrix.columns):
                t_matrix.loc[:, pt] = 0

            # set all transitions to zero that are not in the data
            for pt in set(valid_places) - set(t_matrix.index):
                t_matrix.loc[pt, :] = 0

            # Calculate the probability of transition from one placement type to another
            for pt in t_matrix.columns:
                t_matrix.loc[pt, pt] = 1 - (t_matrix.loc[:, pt].drop(index=pt).sum())

            t_matrix = t_matrix.loc[valid_places, valid_places]

        else:
            # If we have no data, then we assume that the transition matrix is the identity matrix
            t_matrix = pd.DataFrame(
                data=np.eye(len(valid_places)), index=valid_places, columns=valid_places
            )

        transidict[ab] = t_matrix

    return transidict


def get_daily_transitions_new_way(
    df: pd.DataFrame, start_date: date, end_date: date
) -> Dict[AgeBracket, pd.DataFrame]:
    """
    Returns a mapping of the transition rates for each age bracket.

    These are the transition rates for each age bracket.

    This method calls `get_transition_rates()` and then `group_transition_rates()` to groups the transition rates by age bracket.

    :param df: The dataframe containing the data
    :param start_date: The start date of the window to calculate rates for
    :param end_date: The end date of the window to calculate rates for
    :return: A mapping of age bracket to transition rates

    """
    transition_rates = get_transition_rates(df, start_date, end_date)
    return group_transition_rates(transition_rates)
