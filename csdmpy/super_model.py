import pandas as pd

from .utils import truncate, get_ongoing, make_date_index, to_datetime, split_age_bin
from csdmpy.config import age_brackets as bin_defs


def the_model_itself(df, start_date, end_date, horizon_date, step, bin_defs=bin_defs):
    historic_pop = make_populations_ts(df, bin_defs, start_date, end_date)
    date_index = make_date_index(end_date, horizon_date, step).index

    future_pop = pd.DataFrame(columns=historic_pop.columns,
                              index=date_index)
    print('* * * * * * HISTORIC POPS')
    print(historic_pop.to_string())
    print('* * * * * * FUTURE POPS')
    print(future_pop.to_string())
    # set up model:
    transitions_dict = transition_probs_per_bracket(df, bin_defs, start_date, end_date)

    print('* * * * * Transition probabilities for each bin\n')
    for bracket, t_mat in transitions_dict.items():
        print(str(bracket) + ':', t_mat, sep='\n')

    entrance = daily_entrants_per_bracket(df, bin_defs, start_date, end_date)
    print(f'* * ****%%%ENTRANTS:\n')
    for bracket, entra in entrance.items():
        print(str(bracket) + ':', entra, sep='\n')

    next_pop = historic_pop.loc[historic_pop.index.max()].copy()
    entrants_dict = 0
    print(f'* * >>>> * * INITIAL POP\n{next_pop.to_string()}')
    for date in future_pop.index:
        print(f"****DATE:{date}")
        next_pop = apply_ageing(next_pop)
        next_pop = apply_transitions(next_pop, transitions_dict)
        for ab, pt in next_pop.index:
            next_pop[ab, pt] = next_pop[ab, pt] + entrance[ab][pt]
        future_pop.loc[date] = next_pop

    return historic_pop, future_pop # now we can convert these to csv/whatever and send to the frontend


def apply_ageing(next_pop, step_size=None):
    return next_pop


def apply_transitions(next_pop, transitions_dict):
    return next_pop


def apply_entrants(next_pop, entrants_dict):
    return next_pop

def ageing_probs_per_bracket(bin_defs, step_size):
    ageing_mats = {}

    def step_to_days(step_size):
        """Converts as step_size string to an int number of calendar days. 
        A month  is approximated as 30 days"""
        day_units = {'d': 1,
                    'w': 7,
                    'm': 30,
                    'y': 365}
        count, unit = step_size[:-1], step_size[-1].lower()
        count = int(count)
        unit = int(day_units[unit.lower()])
        days = count*unit

        return days

    for age_bin in bin_defs:      
        bin_min, bin_max = tuple(int(bound) for bound in age_bin.split(' to '))
        bin_width_days = (bin_max-bin_min)*365
        step_size_days = step_to_days(step_size)
        aged_out = step_size_days/bin_width_days
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
            _df = df[df['placement_type'].isin(placement_types)]
            trans_rates = get_daily_transition_rates(df, cat_list=placement_types, start_date=start_date,
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
        for placement_type in placement_types:
            entry_rates = get_daily_entrants(this_bin_df, cat=placement_type, cat_list=placement_types,
                                             start_date=start_date, end_date=end_date)
            entrants_mat[age_bin][placement_type] = entry_rates
    return entrants_mat


def make_populations_ts(df, bin_defs, start_date, end_date, step_size='3m', cat_col='placement_type', cat_list=None):
    if cat_list:
        df = df[df[cat_col].isin(cat_list)]
    # make time series of historical placement
    start_date, end_date = to_datetime([start_date, end_date])
    df = truncate(df, start_date, end_date, s_col='DECOM', e_col='DEC')

    ts_info = make_date_index(start_date, end_date, step_size)
    pops_ts = pd.Series(data=ts_info.index,
                        index=ts_info.index)

    pops_ts = pops_ts.apply(lambda date: (get_ongoing(df, date)
                                          .groupby(['age_bin', cat_col])
                                          .size()))

    categories = pd.MultiIndex.from_tuples([(age_bin, place)
                                            for age_bin, place_list in bin_defs.items() for place in place_list])

    discard_cols = set(pops_ts.columns) - set(categories)
    print('>discarding: ', discard_cols)
    add_cols = set(categories) - set(pops_ts.columns)
    print('>adding: ', add_cols)
    pops_ts = pops_ts.drop(columns=discard_cols)
    for col in add_cols:
        pops_ts[col] = 0
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

    entrants = ((df[prev_col] == not_in_care)
        & (df[cat_col] == cat)).sum()

    total_days = (end_date - start_date).days
    entrants = len(df) / total_days

    return entrants
