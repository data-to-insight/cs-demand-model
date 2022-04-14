import pandas as pd
import numpy as np

def truncate(df, start_date, end_date, s_col='DECOM', e_col='DEC'):
    df = df.copy()

    # final column
    df[e_col] = df[e_col].fillna(end_date)

    # only keep  which overlap the specified date range
    df = df[
        (df[s_col] <= end_date)
        & (df[e_col] >= start_date)
    ].copy()

    # for episodes that do overlap, only include the days within the range
    df[s_col] = df[s_col].clip(lower=start_date)
    df[e_col] = df[e_col].clip(upper=end_date)

    return df

def work_out_transition_rates(df, cat, cat_list, start_date=None, end_date=None,
                              cat_col="placement_type", next_col="placement_type_after"):
    s_col = "DECOM"
    e_col = "DEC"

    if start_date is None:
        start_date = df[s_col].min()
    if end_date is None:
        end_date = df[e_col].max()

    try:
        start_date, end_date = pd.to_datetime([start_date, end_date], format='%d/%m/%Y', errors='raise')
    except ValueError:
        start_date, end_date = pd.to_datetime([start_date, end_date], format='%Y-%m-%d', errors='raise')

    if cat not in cat_list:
        raise ValueError("NAUGHTY KITTY: Cat not in list of allowed categories")
    if set(cat_list) < set(df[cat_col].unique()):
        raise ValueError("CAT FIGHT: list of categories supplied disagrees with those found in the data")

    df = df[df[cat_col] == cat]

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col)

    # total number of days of the placement
    divisor = (df[e_col] - df[s_col]).dt.days.sum()

    n_transitions = df.groupby([cat_col, next_col]).size().droplevel(0)
    print(n_transitions)
    trans_rates = n_transitions / divisor
    print(trans_rates)

    # probability of being in the same placement type tomorrow
    # we should change how this works if we want to take into account, say, moving between 2 foster carers
    trans_rates[cat] = 1 - trans_rates.drop(cat).sum()
    print(divisor)
    return n_transitions, trans_rates


def work_out_ingress_rates(df, cat, cat_list, start_date=None, end_date=None,
                      not_in_care="Not in care",
                      cat_col="placement_type", prev_col="placement_type_before"):
    s_col = "DECOM"
    e_col = "DEC"

    if start_date is None:
        start_date = df[s_col].min()
    if end_date is None:
        end_date = df[e_col].max()

    try:
        start_date, end_date = pd.to_datetime([start_date, end_date], format='%d/%m/%Y', errors='raise')
    except ValueError:
        start_date, end_date = pd.to_datetime([start_date, end_date], format='%Y-%m-%d', errors='raise')

    if cat not in cat_list:
        raise ValueError("NAUGHTY KITTY: Cat not in list of allowed categories")
    if not set(cat_list) > set(df[cat_col].unique()):
        raise ValueError("CAT FIGHT: list of categories supplied disagrees with those found in the data")

    df = df[df[cat_col] == cat].copy()

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col)

    df = df[
        (df[prev_col] == not_in_care)
        & (df[cat_col] == cat)
    ]
    denominatrius = (end_date - start_date).days
    entrants = df.groupby([prev_col]).size() / denominatrius

    return entrants


