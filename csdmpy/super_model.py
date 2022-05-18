import pandas as pd

from .utils import truncate, get_ongoing, make_date_index, to_datetime, split_age_bin
from csdmpy.config import age_brackets as bin_defs


def calculate_timestep_transition_matrices(ts_info, daily_t_probs):
    # this makes a dict which maps the step_size in days to
    # the dict of transition matrices for each age_bracket for that many days

    # get the unique step sizes from smallest to largest
    unique_step_sizes = ts_info['step_days'].unique()
    unique_step_sizes.sort()

    # start with the t_probs for one day then add those for each step size present in the time series
    matzo = {1: daily_t_probs}
    for step_days_value in unique_step_sizes:
        step_size_t_probs = matzo[max(matzo)].copy()
        prev_highest = max(matzo)
        print('prev highest', prev_highest)
        while max(matzo) < step_days_value:
            A = max(i for i in matzo.keys() if i < step_days_value)
            B = max(i for i in matzo.keys() if i + A <= step_days_value)
            A_mats = matzo[A]
            B_mats = matzo[B]
            print(f'{A}, {B}: {step_days_value}')
            for age_bracket in step_size_t_probs:
                T = A_mats[age_bracket].dot(B_mats[age_bracket])
                step_size_t_probs[age_bracket] = T
            matzo[A + B] = step_size_t_probs
    return {i: matzo[i] for i in unique_step_sizes}


def apply_ageing(pop, ageing_dict):
    return pop

def step_to_days(step_size):
    """Converts as step_size string to an int number of calendar days. 
    A month  is approximated as 30 days"""
    day_units = {   'd': 1,
                    'w': 7,
                    'm': 30,
                    'y': 365    }
    count, unit = step_size[:-1], step_size[-1].lower()
    count = int(count)
    unit = int(day_units[unit.lower()])
    days = count * unit

    return days

def ageing_probs_per_bracket(bin_defs, step_size):
    ageing_mats = {}

    days = step_to_days(step_size)

    for age_bin in bin_defs:      
        bin_min, bin_max = tuple(int(bound) for bound in age_bin.split(' to '))
        bin_width_days = (bin_max - bin_min) * 365
        step_size_days = step_to_days(step_size)
        aged_out = step_size_days / bin_width_days
        ageing_mats[age_bin] = aged_out
    return ageing_mats


def transition_probs_per_bracket(df, bin_defs, start_date, end_date):
    trans_mats = {}
    for age_bin, placement_types in bin_defs.items():
        if len(placement_types) == 1:
            trans_mats[age_bin] = pd.DataFrame(data=1.0, index=placement_types, columns=placement_types)
        else:
            bin_min, bin_max = split_age_bin(age_bin)
            _df = df[(df['age'] >= bin_min) & (df['age'] < bin_max)]
            _df = _df[_df['placement_type'].isin(placement_types)]
            trans_rates = get_daily_transition_rates(_df, cat_list=placement_types, start_date=start_date,
                                                     end_date=end_date)
            trans_mats[age_bin] = trans_rates
    return trans_mats


def daily_entrants_per_bracket(df, bin_defs, start_date, end_date):
    entrants_mat = {}
    for age_bin in bin_defs:
        entrants_mat[age_bin] = {}
        placement_types = bin_defs[age_bin]
        bin_min, bin_max = split_age_bin(age_bin)
        this_bin_df = df[(df['age'] >= bin_min) & (df['age'] < bin_max)].copy()
        entry_rates = get_daily_entrants(this_bin_df, cat_list=placement_types,
                                             start_date=start_date, end_date=end_date)
        entrants_mat[age_bin] = entry_rates
    return entrants_mat


def make_populations_ts(df, bin_defs, start_date, end_date, step_size='3m', cat_col='placement_type', cat_list=None):
    if cat_list:
        df = df[df[cat_col].isin(cat_list)]
    # make time series of historical placement
    start_date, end_date = to_datetime([start_date, end_date])
    df = truncate(df, start_date, end_date, s_col='DECOM', e_col='DEC')

    ts_info = make_date_index(start_date, end_date, step_size, align_end=True)
    pops_ts = pd.Series(data=ts_info.index,
                        index=ts_info.index)

    pops_ts = pops_ts.apply(lambda date: (get_ongoing(df, date)
                                          .groupby(['age_bin', cat_col])
                                          .size()))

    mind = pd.MultiIndex.from_tuples([(age_bin, place)
                                      for age_bin, place_list in bin_defs.items() for place in place_list])

    discard_cols = set(pops_ts.columns) - set(mind)
    print('>discarding: ', discard_cols)
    add_cols = set(mind) - set(pops_ts.columns)
    print('>adding: ', add_cols)
    pops_ts = pops_ts.drop(columns=discard_cols)
    for col in add_cols:
        pops_ts[col] = 0
    pops_ts = pops_ts.fillna(0)

    print(pops_ts.to_string())

    return pops_ts


def get_daily_transition_rates(df, cat_list=None, start_date=None, end_date=None,
                               cat_col="placement_type", next_col="placement_type_after"):
    print('{}}{{{{{{{{{{{{{{{{ - - IN TRANSFUNC -   }}}}{{{{{{{{{}{}{}{}{}')

    if cat_list is None:
        cat_list = df[cat_col].unique()

    s_col = "DECOM"  # start column
    e_col = "DEC"  # end column

    if start_date is None:
        start_date = df[s_col].min()
    if end_date is None:
        end_date = df[e_col].max()

    start_date, end_date = to_datetime([start_date, end_date])

    df = df.copy()

    # remove episodes that aren't in a relevant category and transferring to a relevant category
    initial_rows = len(df)
    df = df[(df[cat_col].isin(cat_list)) ]#& df[next_col].isin(cat_list)]
    rows_dropped = initial_rows - len(df)

    print(f'dropped {rows_dropped} of {initial_rows} rows due to not being in {cat_list}')

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col, close=True, clip=True)

    # calculate daily probability of transitioning to each placement type
    df['duration'] = (df[e_col] - df[s_col]).dt.days
    total_placement_days = df.groupby(cat_col)['duration'].sum()

    # number of transitions to each placement type
    n_transitions = df.groupby([next_col, cat_col]).size()
    print(n_transitions)
    trans_rates = n_transitions / total_placement_days
    print(trans_rates)

    # probability of being in the same placement type tomorrow
    # (!) we should change how this works if we want to take into account
    #     moves between two placements of the same type
    mind = pd.MultiIndex.from_product([cat_list] * 2)
    for i in mind:
        if i not in trans_rates.index:
            trans_rates.at[i] = 0
            print(f'filling in value for {i} in transitions')
    for cat in cat_list:
        trans_rates.loc[(cat, cat)] = 1 - (trans_rates
                                           .xs(cat, level=1, drop_level=False)
                                           .drop(index=cat, level=0)
                                           .sum())
    print(total_placement_days)

    return trans_rates.unstack().reindex(index=cat_list, columns=cat_list)


def get_daily_entrants(df, cat_list, start_date=None, end_date=None,
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
    df = df.copy()
    #df = df[df[cat_col] == cat].copy()

    # remove episodes starting outside the date range
    df = df[(df['DECOM'] >= start_date) & (df['DECOM'] <= end_date)]

    df = df[df[prev_col] == not_in_care].groupby(cat_col).size()
    nudf = pd.Series(data=0, index=cat_list)
    cols = list(set(df.index) & set(cat_list))
    nudf[cols] = df[cols]

    #entrants = ((df[prev_col] == not_in_care)
    #            & (df[cat_col] == cat)).sum()

    total_days = (end_date - start_date).days
    entrants = nudf / total_days
    print(entrants)
    return entrants.reindex(cat_list)
