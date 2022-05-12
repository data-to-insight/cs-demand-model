import pandas as pd
from .config import ACCEPTED_DATE_FORMATS
import os


def ezfiles():
    test_903_dir = os.path.join(os.path.dirname(__file__), 'tests', 'fake903_5yrs')
    year_list = [2017, 2018, 2019, 2020, 2021]
    tables_needed = ('header', 'episodes')
    table_headers = {
        'Episodes':
            'CHILD,DECOM,RNE,LS,CIN,PLACE,PLACE_PROVIDER,DEC,REC,REASON_PLACE_CHANGE,HOME_POST,PL_POST'.split(','),
        'Header':
            'CHILD,SEX,DOB,ETHNIC,UPN,MOTHER,MC_DOB'.split(',')
    }
    files_list = []
    for year in year_list:
        year_dir = os.path.join(test_903_dir, str(year))
        label = str(max(year_list) - year) + "_ago"
        for table_name in tables_needed:
            table_path = os.path.join(year_dir, table_name + '.csv')
            with open(table_path, 'r') as file:
                file_bytes = file.read().encode('utf-8')
            files_list.append({'description': label,
                               'fileText': file_bytes})
    return files_list


def split_age_bin(age_bin):
    lower, upper = age_bin.split(' to ')
    lower = int(lower)
    upper = int(upper)
    return lower, upper


def to_datetime(dates, date_formats=None):
    if not date_formats:
        date_formats = ACCEPTED_DATE_FORMATS

    good_date = False
    for date_format in date_formats:
        try:
            dates = pd.to_datetime(dates, format=date_format, errors='raise')
            good_date = True
            break
        except ValueError as e:
            caught = e
    if not good_date:
        date_formats = [f'"{i}"' for i in date_formats]
        raise ValueError(f"if passing dates as strings use format " +
                         f"{', '.join(date_formats[:-1])} or {date_formats[-1]}" +
                         f"\nCaught ValueError:\n\t{caught.args[0]}")
    return dates


def make_date_index(start_date, end_date, step_size, align_end=False):
    start_date, end_date = to_datetime([start_date, end_date])
    date_units = {'d': 'days',
                  'w': 'weeks',
                  'm': 'months',
                  'y': 'years'}
    count, unit = step_size[:-1], step_size[-1]
    count = int(count)
    unit = date_units[unit.lower()]
    step_off = pd.DateOffset(**{unit: count})

    ts_info = pd.DataFrame(columns=['step_days'])

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


def truncate(df, start_date, end_date, s_col='DECOM', e_col='DEC', close=False, clip=False):
    df = df.copy()

    if close:
        # end open episodes at the end date
        df[e_col] = df[e_col].fillna(end_date)

    # only keep episodes which overlap the specified date range
    df = df[
        (df[s_col] <= end_date)
        & ((df[e_col] >= start_date) | df[e_col].isna())
    ].copy()

    if clip:
        # for episodes that do overlap, only include the days within the range
        df[s_col] = df[s_col].clip(lower=start_date)
        df[e_col] = df[e_col].clip(upper=end_date)
    return df


def get_ongoing(df, t, s_col='DECOM', e_col='DEC', censor=False, retrospective_cols=None):
    df = df[(df[s_col] <= t)
            & ((df[e_col] > t) | df[e_col].isna())].copy()
    if censor:
        df.loc[(df[e_col] > t), e_col] = pd.NaT
        if retrospective_cols:
            df.loc[(df[e_col] > t), retrospective_cols] = pd.NA
    return df
