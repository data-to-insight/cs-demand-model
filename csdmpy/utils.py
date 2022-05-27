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

def deviation_bounds(data, variance_values):
    """ This function adds and subtracts 1 standard deviation to calculate the uppper and lower bounds, respectively, of data provided to it.  """

    # get the average variance of each variable.
    var_sums = variance_values.mean(axis=0)
    # standard deviation = square_root(variances)
    standard_deviations = var_sums.apply(lambda x : x**0.5)
    
    upper_values = data.copy()
    lower_values = data.copy()
    for column_name in data.columns:
        upper_values[column_name] = upper_values[column_name] + standard_deviations[column_name]
        lower_values[column_name] = lower_values[column_name] - standard_deviations[column_name]

    return upper_values, lower_values

def _nest_dict_rec(key, value, out):
    """ Recursive function that keeps splitting until all the nested values have been formed. """
    
    key, *everything_else = key.split('_', 1)
    if everything_else:
        _nest_dict_rec(everything_else[0], value, out.setdefault(key, {}))
    else:
        out[key] = value

def flat_to_nested(flat_dict):
    """This function converts flat dictionaries, provided by the frontend, into nested dictionaries which the backend needs."""

    # specify the data type of the resulting nested structure.
    result = {}
    for key, value in flat_dict.items():
        # categories that do not have any subkeys are provided subcategories of the same name.
        # 'Supported': 40 becomes 'Supported':{'Supported': 40}
        if '_' not in key:
            key += '_' + key
        _nest_dict_rec(key, value, result)
    return result

def assign_value(nested_dict, val):
    """ 
    structure of parameters expected.
    nested_dict =  {'Fostering': {'friend/relative': None}}
    value = an integer e.g 17

    function returns
    {'Fostering': {'friend/relative': 17}}

    """
    for i, j in result.items():
        # i is a key, j is a dictionary.
        for k in j.keys():
            # k is the key in the inner dictionary.
            result[i][k] = val
            break
    return nested_dict
    

def param_handover(key_mapping_dict, param_dict):
    """
    ## Inputs
    key_mapping_dict (dict mapping keys of param_dict to keys of costs_dict)
    param_dict (flat dict containing (among other things) costs and proportions, for each subcategory)
     
    ## Returns.
    costs_params (dict of params for calculate_costs  - cost_dict, proportions, , inflation (expect none, false, or float), step_size)

    in addition to the subcateogries mentioned above, the param_dict will contain 'step_size', 'inflation', the subcategories proportions - probably the same as the category names but with `' proportion' at the end
    """
    # get all the keys in param_dict that match cost params in the key_mapping dict.
    # separate them out into the cost values and the proportion values.
    # proportions: remove the proportion suffix 
    # both: assign the values and return the nested proportions and costs dictionaries and then everything that was not selected out of param_dict.

flat_dict = {
    'Fostering (friend/relative)': 11,
    'Fostering (in-house)': 12,
    'Fostering (IFA)': 13,
    'Residential (in-house)': 14,
    'Residential (external)': 15,
    'Supported': 16,
    'Secure home': 17,
    'Placed with family': 18,
    'Other': 19
}


def cost_translation(costs_input, proportions_input, mapping_dict):
    costs_output = {}

    def flat_to_nest(input, mapping_dict):
        output = {}
        for key, value in mapping_dict.items():
            category, subcategory = value
            if category in output:
                output[category][subcategory] = input[key]
            else:
                output[category] = {}
                output[category][subcategory] = input[key]
        return output

    costs_output = flat_to_nest(costs_input, mapping_dict)
    proportions_output = flat_to_nest(proportions_input, mapping_dict)

    return costs_output, proportions_output