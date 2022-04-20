import pandas as pd

from .utils import truncate, get_ongoing, make_date_index, to_datetime

bin_defs = {
    (-1, 1): ('Foster', ),
    (1, 5): ('Foster', ),
    (5, 10): ('Foster', 'Resi'),
    (10, 16): ('Foster', 'Resi'),
    (16, 18): ('Foster', 'Resi', 'Supported'),
}


def transition_probs_per_bracket(df, bin_defs, start_date, end_date):
    trans_mats = {}
    for age_bin, placement_types in bin_defs.items():
        if len(placement_types) == 1:
            trans_mats[age_bin] = pd.DataFrame(data=1.0, index=placement_types, columns=placement_types)
        else:
            bin_min, bin_max = age_bin
            #transition_matrix = pd.DataFrame(index=placement_types, columns=placement_types)
            _df = df[(df['age'] >= bin_min) & (df['age'] < bin_max)]
            _df = df[df['placement_type'].isin(placement_types)]
            trans_rates = get_daily_transition_rates(df, cat_list=placement_types, start_date=start_date,
                                                     end_date=end_date)
            trans_mats[age_bin] = trans_rates
    return trans_mats


def make_populations_ts(df, bin_defs, start_date, end_date, step_size='3m', cat_col='placement_type', cat_list=None):
    if cat_list:
        df = df[df[cat_col].isin(cat_list)]
    # make time series of historical placement
    start_date, end_date = to_datetime([start_date, end_date])
    df = truncate(df, start_date, end_date, s_col='DECOM', e_col='DEC')

    ts_info = make_date_index(start_date, end_date, step_size)
    pops_ts = pd.Series(data=ts_info.index,
                        index=ts_info.index)
    pops_ts = pops_ts.apply(lambda date: get_ongoing(df, date)
                                         .groupby([cat_col, 'age_bin'])
                                         .size())
    pops_ts = pops_ts.fillna(0)

    return pops_ts


def get_daily_transition_rates(df, cat_list=None, start_date=None, end_date=None,
                               cat_col="placement_type", next_col="placement_type_after"):

    if cat_list is None:
        cat_list = df[cat_col].unique()

    s_col = "DECOM"  # start column
    e_col = "DEC"  # end column

    if start_date is None:
        start_date = df[s_col].min()
    if end_date is None:
        end_date = df[e_col].max()

    start_date, end_date = to_datetime([start_date, end_date])

    # remove episodes
    df = df.copy()
    df = df[(df[cat_col].isin(cat_list)) & df[next_col].isin(cat_list)]

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col)

    # calculate daily probability of transitioning to each placement type
    total_placement_days = (df[e_col] - df[s_col]).dt.days.sum()

    # number of transitions to each placement type
    # TODO: make this per placement type, not entire df
    n_transitions = df.groupby([next_col, cat_col]).size()
    print(n_transitions)
    trans_rates = n_transitions / total_placement_days
    print(trans_rates)

    # probability of being in the same placement type tomorrow
    # (!) we should change how this works if we want to take into account
    # moves between two placements of the same type
    for cat in cat_list:
        trans_rates.loc[(cat, cat)] = 1 - (trans_rates
                                          .xs(cat, level=1, drop_level=False)
                                          .drop(index=cat, level=0)
                                          .sum())
    print(total_placement_days)
    return trans_rates


def get_daily_entrants(df, cat, cat_list, start_date=None, end_date=None,
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
