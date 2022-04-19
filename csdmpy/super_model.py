import pandas as pd

from .utils import truncate, get_ongoing, make_date_index, to_datetime


def make_pops_ts(df, start_date, end_date, step_size='3m', cat_col='placement_type'):
    # make time series of historical placement
    start_date, end_date = to_datetime([start_date, end_date])
    df = truncate(df, start_date, end_date, s_col='DECOM', e_col='DEC')

    ts_info = make_date_index(start_date, end_date, step_size)
    pops_ts = pd.Series(data=ts_info.index,
                        index=ts_info.index).apply(lambda date: get_ongoing(df, date)
                                                                .groupby(cat_col)
                                                                .size())
    pops_ts = pops_ts.fillna(0)

    return pops_ts, ts_info


def work_out_transition_rates(df, cat=None, cat_list=None, start_date=None, end_date=None,
                              cat_col="placement_type", next_col="placement_type_after"):
    """

    :param df:
    :param cat:
    :param cat_list:
    :param start_date:
    :param end_date:
    :param cat_col:
    :param next_col:
    :return:
    """
    if cat_list is None:
        cat_list = df[cat_col].unique()

    s_col = "DECOM"  # start column
    e_col = "DEC"  # end column

    if start_date is None:
        start_date = df[s_col].min()
    if end_date is None:
        end_date = df[e_col].max()

    start_date, end_date = to_datetime([start_date, end_date])

    if cat not in cat_list:
        raise ValueError(f"Category '{cat}' not in list of allowed categories: {cat_list}")
    if not set(cat_list).issuperset(set(df[cat_col].unique())):
        raise ValueError("List of categories supplied disagrees with those found in the data. \n"
                         f"Supplied: {cat_list}\n Inferred: {df[cat_col].unique()}")

    if cat != 'all':
        df = df[df[cat_col] == cat]
    df = df.copy()

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col)

    # calculate daily probability of transitioning to each placement type
    total_placement_days = (df[e_col] - df[s_col]).dt.days.sum()

    # number of transitions to each placement type
    n_transitions = df.groupby([cat_col, next_col]).size().droplevel(0)
    print(n_transitions)
    trans_rates = n_transitions / total_placement_days
    print(trans_rates)

    # probability of being in the same placement type tomorrow
    # (!) we should change how this works if we want to take into account
    # moves between two placements of the same type
    trans_rates[cat] = 1 - trans_rates.drop(cat).sum()
    print(total_placement_days)
    return n_transitions, trans_rates


def work_out_daily_entrants(df, cat, cat_list, start_date=None, end_date=None,
                           not_in_care="Not in care",
                           cat_col="placement_type", prev_col="placement_type_before"):
    s_col = "DECOM"
    e_col = "DEC"

    if start_date is None:
        # (!) this will result in underestimating the ingress rates
        start_date = df[s_col].min()
    if end_date is None:
        end_date = df[e_col].max()

    start_date, end_date = to_datetime([start_date, end_date])

    df = df[df[cat_col] == cat].copy()

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col)

    df = df[
        (df[prev_col] == not_in_care)
        & (df[cat_col] == cat)
    ]

    total_days = (end_date - start_date).days
    entrants = df.groupby([prev_col]).size() / total_days

    return entrants
