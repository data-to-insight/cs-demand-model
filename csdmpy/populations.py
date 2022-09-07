from datetime import date

import pandas as pd

from csdmpy.constants import AgeBracket
from csdmpy.timeseries import StepSize, make_date_index, time_truncate


def _get_ongoing(df, dt: date):
    """
    Get all the ongoing placements for a given date.
    """
    return df[(df["DECOM"] <= dt) & ((df["DEC"] > dt) | df["DEC"].isna())]


def make_populations_ts(
    df, start_date: date, end_date: date, step_size: StepSize, cat_col="placement_type"
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

    """
    - columns which are only present in pops_ts will be ignored. There is no longer need to explicitly discard.
    - all columns needed would have been created in populations_ts. There is no longer need to explicitly add.
    - the fillna will assign all missing values to zero. There is no longer need to do this for the extra columns.
    - The DataFrame generated will have all column names (age bins) in natural order.
    """
    populations_ts.fillna(0, inplace=True)

    return populations_ts
