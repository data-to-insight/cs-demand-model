from datetime import date

import pandas as pd

from csdmpy.constants import IntervalUnit


class StepSize:
    """
    Represents a step-size for a time-series.
    """

    def __init__(self, interval: int, unit: IntervalUnit):
        self.__interval = interval
        self.__unit = unit

    @property
    def interval(self) -> int:
        return self.__interval

    @property
    def unit(self) -> IntervalUnit:
        return self.__unit

    @property
    def pandas_offset(self) -> pd.DateOffset:
        return pd.DateOffset(**{self.unit.label: self.interval})


def make_date_index(
    start_date: date, end_date: date, step_size: StepSize, align_end=False
):
    step_off = step_size.pandas_offset
    ts_info = pd.DataFrame(columns=["step_days"])

    # TODO: Why not use pd.date_range?

    if align_end:
        date = end_date
        while date >= start_date:
            ts_info.loc[date, "step_days"] = ((date + step_off) - date).days
            date -= step_off
    else:
        date = start_date
        while date <= end_date:
            ts_info.loc[date, "step_days"] = ((date + step_off) - date).days
            date += step_off

    return ts_info.sort_index()


def time_truncate(
    df: pd.DataFrame,
    start_date: date,
    end_date: date,
    s_col="DECOM",
    e_col="DEC",
    close=False,
    clip=False,
) -> pd.DataFrame:
    """
    Truncate a time-series dataframe to a given start and end date.

    :param df: The dataframe to truncate.
    :param start_date: The start date.
    :param end_date: The end date.
    :param s_col: The column name for the period start. Defaults to DECOM
    :param e_col: The column name for the period end. Defaults to DEC
    :param close: If True, the start and end dates are included in the truncated dataframe.
    :param clip: If True, the start and end dates are clipped to the dataframe start and end dates.

    WARNING: Modifies the dataframe in-place.
    """

    if close:
        # end open episodes at the end date
        df[e_col] = df[e_col].fillna(end_date)

    # only keep episodes which overlap the specified date range
    df = df[(df[s_col] <= end_date) & ((df[e_col] >= start_date) | df[e_col].isna())]

    if clip:
        # for episodes that do overlap, only include the days within the range
        df[s_col] = df[s_col].clip(lower=start_date)
        df[e_col] = df[e_col].clip(upper=end_date)

    return df
