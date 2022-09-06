import pandas as pd

from csdmpy.constants import IntervalUnit
from csdmpy.timeseries import StepSize, make_date_index


def test_day():
    start_date = pd.to_datetime('2020-01-01')
    end_date = pd.to_datetime('2020-01-08')

    step_size = StepSize(1, IntervalUnit.DAY)
    ts_info = make_date_index(start_date, end_date, step_size, align_end=False)
    assert ts_info.index.to_list() == [
        pd.to_datetime('2020-01-01'),
        pd.to_datetime('2020-01-02'),
        pd.to_datetime('2020-01-03'),
        pd.to_datetime('2020-01-04'),
        pd.to_datetime('2020-01-05'),
        pd.to_datetime('2020-01-06'),
        pd.to_datetime('2020-01-07'),
        pd.to_datetime('2020-01-08'),
    ]

    ts_info = make_date_index(start_date, end_date, step_size, align_end=True)
    assert ts_info.index.to_list() == [
        pd.to_datetime('2020-01-01'),
        pd.to_datetime('2020-01-02'),
        pd.to_datetime('2020-01-03'),
        pd.to_datetime('2020-01-04'),
        pd.to_datetime('2020-01-05'),
        pd.to_datetime('2020-01-06'),
        pd.to_datetime('2020-01-07'),
        pd.to_datetime('2020-01-08'),
    ]

    step_size = StepSize(2, IntervalUnit.DAY)
    ts_info = make_date_index(start_date, end_date, step_size, align_end=False)
    assert ts_info.index.to_list() == [
        pd.to_datetime('2020-01-01'),
        pd.to_datetime('2020-01-03'),
        pd.to_datetime('2020-01-05'),
        pd.to_datetime('2020-01-07'),
    ]

    ts_info = make_date_index(start_date, end_date, step_size, align_end=True)
    assert ts_info.index.to_list() == [
        pd.to_datetime('2020-01-02'),
        pd.to_datetime('2020-01-04'),
        pd.to_datetime('2020-01-06'),
        pd.to_datetime('2020-01-08'),
    ]


def test_week():
    start_date = pd.to_datetime('2020-01-01')
    end_date = pd.to_datetime('2020-02-28')

    step_size = StepSize(1, IntervalUnit.WEEK)
    ts_info = make_date_index(start_date, end_date, step_size, align_end=False)
    assert ts_info.index.to_list() == [
        pd.to_datetime('2020-01-01'),
        pd.to_datetime('2020-01-08'),
        pd.to_datetime('2020-01-15'),
        pd.to_datetime('2020-01-22'),
        pd.to_datetime('2020-01-29'),
        pd.to_datetime('2020-02-05'),
        pd.to_datetime('2020-02-12'),
        pd.to_datetime('2020-02-19'),
        pd.to_datetime('2020-02-26'),
    ]

    step_size = StepSize(1, IntervalUnit.WEEK)
    ts_info = make_date_index(start_date, end_date, step_size, align_end=True)
    assert ts_info.index.to_list() == [
        pd.to_datetime('2020-01-03'),
        pd.to_datetime('2020-01-10'),
        pd.to_datetime('2020-01-17'),
        pd.to_datetime('2020-01-24'),
        pd.to_datetime('2020-01-31'),
        pd.to_datetime('2020-02-07'),
        pd.to_datetime('2020-02-14'),
        pd.to_datetime('2020-02-21'),
        pd.to_datetime('2020-02-28'),
    ]