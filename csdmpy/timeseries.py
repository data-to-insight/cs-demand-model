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


def make_date_index(start_date: date, end_date: date, step_size: StepSize, align_end=False):
    step_off = step_size.pandas_offset
    ts_info = pd.DataFrame(columns=['step_days'])

    # TODO: Why not use pd.date_range?

    if align_end:
        date = end_date
        while date >= start_date:
            ts_info.loc[date, 'step_days'] = ((date + step_off) - date).days
            date -= step_off
    else:
        date = start_date
        while date <= end_date:
            ts_info.loc[date, 'step_days'] = ((date + step_off) - date).days
            date += step_off

    return ts_info.sort_index()
