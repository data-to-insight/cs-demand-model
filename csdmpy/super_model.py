import pandas as pd

from .utils import truncate, get_ongoing, make_date_index, to_datetime, split_age_bin
from csdmpy.config import age_brackets as bin_defs
from csdmpy.config import NOT_IN_CARE
from csdmpy.utils import truncate

import numpy as np

def get_default_proportions(df, start=None, end=None,):
    if not start:
        # use the earliest date in the data as the default start date.
        start = df[['DECOM', 'DEC']].min().min()
    if not end:
        # use the latest date in the data as the defualt end date.
        end = df[['DECOM', 'DEC']].max().max()

    # get only the episodes that exist in the reference period.
    # clip so that episode days which exist out of period are not considered.
    ref_df = truncate(df.copy(), start_date=start, end_date=end, close=True, clip=True)

    """For each day, the proportion split among subplacement types consists of dividing the 
    number of children in each subplacement by the total number of children in that placement on that day.
    Hence for x days, the proportion split will be the number of days spent in each subplacement divided by 
    the number of days recorded in the placement by all the episodes which occurred during x days."""

    ref_df['days_in_place'] = (ref_df['DEC'] - ref_df['DECOM']).dt.days

    # count the number of subplacements in the period.
    subplacements = ref_df.groupby(['placement_type', 'placement_subtype'])['days_in_place'].sum()
    
    # calculate how subplacements are proportional to main placements.
    subplacements = subplacements.groupby(level=0).transform(lambda x: (x / x.sum()).round(3)) 
    """3 decimal places have a lower tendency to sum up to more than 1 than if the results were rounded to 2 decimal places.
    Try setting the reference period to 01/06/2016 - 01/06/2017 to replicate the bug where the sum passes 1 because of rounding up."""
    
    """TODO what happpens when a subplacement is calculated to have a proportion of zero?. Should something happen?
        Fill in zero for missing proportions so that they do not flag an error in the frontend."""
    # convert to expected format: flat dictionary.
    subplacements.index = subplacements.index.droplevel(level=0)
    default_props = subplacements.to_dict()

    return default_props

def get_daily_pops_new_way(df, start=None, end=None, bin_defs=None):
    if not start:
        start = df[['DECOM', 'DEC']].min().min()
    if not end:
        end = df[['DECOM', 'DEC']].max().max()

    endings = df.groupby(['DEC', 'placement_type', 'age_bin']).size()
    endings.name = 'nof_decs'

    beginnings = df.groupby(['DECOM', 'placement_type', 'age_bin']).size()
    beginnings.name = 'nof_decoms'

    endings.index.names = ['date', 'placement_type', 'age_bin']
    beginnings.index.names = ['date', 'placement_type', 'age_bin']

    pops = pd.merge(left=beginnings, right=endings,
                    left_index=True, right_index=True, how='outer')

    pops = (pops
            .fillna(0)
            .sort_values('date'))

    pops = ((pops['nof_decoms'] - pops['nof_decs'])
            .groupby(['placement_type', 'age_bin'])
            .cumsum()
            .unstack(['age_bin', 'placement_type'])
            .resample('D')
            .fillna(method='ffill')  # this one does nothing? as freq something
            .fillna(method='ffill')
            .truncate(before=start, after=end)
            .fillna(0))
    return pops


def get_daily_transitions_new_way(df, pops, bin_defs=bin_defs):
    #df['DEC'] = pd.DateOffset(days=1)
    transitions = (df
                   .groupby(['placement_type', 'placement_type_after', 'age_bin', 'DEC'])
                   .size()
                   .unstack(level=['age_bin', 'placement_type', 'placement_type_after'])
                   .truncate(before=pops.index.min(), after=pops.index.max())
                   .fillna(0)
                   .asfreq('D', fill_value=0)
                  # .stack('placement_type_after')
                   # .reorder_levels(['DEC','placement_type_after',  ])
                   )

    popal, transal = pops.align(transitions)

    print('~~~~~~~~~~~~~~~~~~~\n~ ~ ~ ~ ~ ~ ~ ~ ~ ~\n',
          transitions['16 to 18', 'Resi', 'Supported'].apply(['min', 'max']))
    print(((transitions['16 to 18', 'Resi', 'Supported'] != 0) & (pops['16 to 18', 'Resi'] == 0)).any().any())
    trans_nonz = (transal['16 to 18', 'Resi', 'Supported'] != 0)
    pops_zero = (popal['16 to 18', 'Resi', 'Supported'] == 0)

    print((trans_nonz & pops_zero).any())
    print('POPS\n',popal[trans_nonz & pops_zero].to_string())
    print('TRANS\n', transal[trans_nonz & pops_zero].to_string())

    #print(born_slippy.index)
    #print(transitions.loc[_s[born_slippy.any(axis=1)], :], sep='\n==============\n'*2)
    #print(born_slippy.any(axis=1))

    transition_rates = ((transal / popal.shift(1).fillna(method='bfill'))
                        .mean(axis=0)
                        .unstack(['age_bin', 'placement_type'])
                        .fillna(0))

    bins_in_data = transition_rates.columns.get_level_values('age_bin').unique()
    transidict = {}
    for ab in bin_defs:
        valid_places = bin_defs[ab]
        if ab in bins_in_data:
            t_matrix = transition_rates[ab].copy()
            for pt in t_matrix.columns:
                print('-------->', pt, '<---')
                t_matrix.loc[pt, pt] = 1 - (t_matrix
                                            .loc[:, pt]
                                            .drop(index=pt)
                                            .sum())
            t_matrix = t_matrix.loc[valid_places, valid_places]
        else:
            t_matrix = pd.DataFrame(data=np.eye(len(valid_places)),
                                    index=valid_places,
                                    columns=valid_places)
        print(t_matrix.to_string())
        transidict[ab] = t_matrix
    return transidict


def calculate_timestep_transition_matrices(ts_info, daily_t_probs):
    # this makes a dict which maps the step_size in days to
    # the dict of transition matrices for each age_bracket for that many days

    # get the unique step sizes from smallest to largest
    unique_step_sizes = ts_info['step_days'].unique()
    unique_step_sizes.sort()

    # start with the t_probs for one day then add those for each step size present in the time series
    step_size_t_probs_dict = {1: daily_t_probs}
    for step_days_value in unique_step_sizes:
        step_size_t_probs = step_size_t_probs_dict[max(step_size_t_probs_dict)].copy()
        prev_highest = max(step_size_t_probs_dict)
        print('prev highest', prev_highest)
        while max(step_size_t_probs_dict) < step_days_value:
            A = max(i for i in step_size_t_probs_dict.keys() if i < step_days_value)
            B = max(i for i in step_size_t_probs_dict.keys() if i + A <= step_days_value)
            A_mats = step_size_t_probs_dict[A]
            B_mats = step_size_t_probs_dict[B]
            print(f'{A}, {B}: {step_days_value}')
            for age_bracket in step_size_t_probs:
                T = A_mats[age_bracket].dot(B_mats[age_bracket])
                step_size_t_probs[age_bracket] = T
            step_size_t_probs_dict[A + B] = step_size_t_probs
    return {i: step_size_t_probs_dict[i] for i in unique_step_sizes}


def apply_ageing(pop, ageing_dict):
    return pop


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
    days = count * unit

    return days


def ageing_probs_per_bracket(bin_defs, step_size):
    ageing_ratios = {}
    for age_bin in bin_defs:
        bin_min, bin_max = split_age_bin(age_bin)
        bin_width_days = (bin_max - bin_min) * 365
        step_size_days = step_to_days(step_size)
        aged_out = step_size_days / bin_width_days
        ageing_ratios[age_bin] = aged_out
    return ageing_ratios


def transition_probs_per_bracket(df, bin_defs, start_date, end_date):
    trans_mats = {}
    for age_bin, placement_types in bin_defs.items():
        if len(placement_types) == 1:
            trans_mats[age_bin] = pd.DataFrame(
                data=1.0, index=placement_types, columns=placement_types
            )
        else:
            bin_min, bin_max = split_age_bin(age_bin)
            _df = df[(df["age"] >= bin_min) & (df["age"] < bin_max)]
            _df = _df[_df["placement_type"].isin(placement_types)]
            trans_rates = get_daily_transition_rates(
                _df, cat_list=placement_types, start_date=start_date, end_date=end_date
            )
            trans_mats[age_bin] = trans_rates
    return trans_mats


def daily_entrants_per_bracket(df, bin_defs, start_date, end_date):
    entrants_mat = {}
    for age_bin in bin_defs:
        entrants_mat[age_bin] = {}
        placement_types = bin_defs[age_bin]
        bin_min, bin_max = split_age_bin(age_bin)
        this_bin_df = df[(df["age"] >= bin_min) & (df["age"] < bin_max)].copy()
        entry_rates = get_daily_entrants(this_bin_df, cat_list=placement_types,
                                         start_date=start_date, end_date=end_date)
        entrants_mat[age_bin] = entry_rates
    return entrants_mat


def make_populations_ts(df, bin_defs, start_date, end_date, step_size='3m', cat_col='placement_type', cat_list=None):
    if cat_list:
        df = df[df[cat_col].isin(cat_list)]
    # make time series of historical placement
    start_date, end_date = to_datetime([start_date, end_date])
    df = truncate(df, start_date, end_date, s_col="DECOM", e_col="DEC")

    ts_info = make_date_index(start_date, end_date, step_size, align_end=True)
    pops_ts = pd.Series(data=ts_info.index, index=ts_info.index)

    pops_ts = pops_ts.apply(lambda date: (get_ongoing(df, date)
                                          .groupby(['age_bin', cat_col])
                                          .size()))

    multi_ind = pd.MultiIndex.from_tuples(
        [
            (age_bin, place)
            for age_bin, place_list in bin_defs.items()
            for place in place_list ],
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

    print(populations_ts.to_string())

    return populations_ts


def get_daily_transition_rates(df, cat_list=None, start_date=None, end_date=None,
                               cat_col="placement_type", next_col="placement_type_after"):
    print('{}}{{{{{{{{{{{{{{{{ - - IN TRANSFUNC -   }}}}{{{{{{{{{}{}{}{}{}')

    if cat_list is None:
        cat_list = df[cat_col].unique()

    #if NOT_IN_CARE not in cat_list:
    #    cat_list = list(cat_list) #+ [NOT_IN_CARE,]

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
    df = df[(df[cat_col].isin(cat_list))]  # & df[next_col].isin(cat_list)]
    rows_dropped = initial_rows - len(df)

    print(f'dropped {rows_dropped} of {initial_rows} rows due to not being in {cat_list}')

    # remove episodes outside the date range and truncate episodes extending beyond it
    df = truncate(df, start_date, end_date, s_col, e_col, close=True, clip=True)

    # calculate daily probability of transitioning to each placement type
    df["duration"] = (df[e_col] - df[s_col]).dt.days
    total_placement_days = df.groupby(cat_col)["duration"].sum()

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
            print(f"filling in value for {i} in transitions")
    for cat in cat_list:
        trans_rates.loc[(cat, cat)] = 1 - (trans_rates
                                           .xs(cat, level=1, drop_level=False)
                                           .drop(index=cat, level=0)
                                           .sum())
    print(trans_rates)
    #trans_rates.drop(columns=NOT_IN_CARE, index=NOT_IN_CARE)
    print(total_placement_days)

    return trans_rates.unstack().reindex(index=cat_list, columns=cat_list)


def get_daily_entrants(df, cat_list, start_date=None, end_date=None,
                       not_in_care=NOT_IN_CARE,
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
    df = df[(df[s_col] >= start_date) & (df[s_col] <= end_date)]

    df = df[df[prev_col] == not_in_care].groupby(cat_col).size()
    nudf = pd.Series(data=0, index=cat_list)
    cols = list(set(df.index) & set(cat_list))
    nudf[cols] = df[cols]

    total_days = (end_date - start_date).days
    entrants = nudf / total_days
    print(entrants)
    return entrants.reindex(cat_list)


def apply_adjustments(pops, adjustments, step_days):
    # TODO: make sure there is at most one adjustment moving kids from one category to another (?)
    # TODO: when more kids than population moving from a category, spread them among all destination categories
    # TODO: calculate relative adjustments from unadjusted population
    # adjustments = pd.DataFrame(adjustments)
    # ...
    print(', @@@ BEFORE ADJUSTING@ @ @ @',pops)

    for adj in adjustments:
        age = adj['age']
        moving_from = adj['from']
        moving_to = adj['to']
        amount = int(adj['n']) * step_days / 30.44
        adjustment_type = 'absolute'  # adj['adjustment_type']
        if adjustment_type == 'absolute' and moving_from != 'New care entrant':
            amount = min(amount, pops[age, moving_from])
        elif adjustment_type == 'relative':
            amount = amount * pops[moving_from]
        if moving_to != 'Care leaver':
            pops[(age, moving_to)] += amount
        if moving_from != 'New care entrant':
            pops[(age, moving_from)] -= amount
    print(',.,.,, AFTER ADJUSTING @@@ @ @ @ @', pops)

    return pops
