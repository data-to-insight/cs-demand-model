from datetime import date

import numpy as np
import pandas as pd

from csdmpy.constants import AgeBracket
from csdmpy.timeseries import StepSize, make_date_index, time_truncate


def _get_ongoing(df, dt: date):
    """
    Get all the ongoing placements for a given date.
    """
    return df[(df["DECOM"] <= dt) & ((df["DEC"] > dt) | df["DEC"].isna())]


def make_populations_ts(
    df, start_date: date, end_date: date, step_size: StepSize = StepSize.DEFAULT, cat_col="placement_type"
):
    df = time_truncate(df, start_date, end_date)
    ts_info = make_date_index(start_date, end_date, step_size, align_end=True)

    pops_ts = pd.Series(data=ts_info.index, index=ts_info.index)
    pops_ts = pops_ts.apply(
        lambda dt: _get_ongoing(df, dt).groupby(["age_bin", cat_col]).size()
    )

    multi_ind = pd.MultiIndex.from_tuples(
        [(a.label, place) for a in AgeBracket for place in a.placement_categories],
        names=("age_bin", "placement_type"),
    )

    # create a superset DataFrame that has all the possible column names (placement_type - age_bin combinations)
    populations_ts = pd.DataFrame(index=pops_ts.index, columns=multi_ind)
    populations_ts.update(pops_ts)

    # - columns which are only present in pops_ts will be ignored. There is no longer need to explicitly discard.
    # - all columns needed would have been created in populations_ts. There is no longer need to explicitly add.
    # - the fillna will assign all missing values to zero. There is no longer need to do this for the extra columns.
    # - The DataFrame generated will have all column names (age bins) in natural order.

    populations_ts.fillna(0, inplace=True)

    return populations_ts


def _group_and_count_dates(df: pd.DataFrame, column: str, name: str) -> pd.Series:
    """
    Group the DataFrame by the given column and count the number of rows in each group.
    """
    groups = df.groupby([column, "placement_type", "age_bin"]).size()
    groups.name = name
    groups.index.names = ["date", "placement_type", "age_bin"]
    return groups


def get_daily_pops_new_way(df, start_date: date, end_date: date):
    """
    Calculates the daily population for each age bin and placement type by
    finding all the transitions (start or end of episode), summing to get total populations for each
    day and then resampling to get the daily populations.
    """
    beginnings = _group_and_count_dates(df, "DECOM", "nof_decoms")
    endings = _group_and_count_dates(df, "DEC", "nof_decs")

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
