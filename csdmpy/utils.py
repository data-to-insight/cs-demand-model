import pandas as pd
from .config import ACCEPTED_DATE_FORMATS, cost_params_map
import os
from warnings import warn


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
    print('######################################################\n', df)
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


def cost_translation(costs_input, proportions_input, mapping_dict):
    costs_output = {}

    costs_output = flat_to_nest(costs_input, mapping_dict)
    proportions_output = flat_to_nest(proportions_input, mapping_dict)

    return costs_output, proportions_output


def flat_to_nest(flat, mapping_dict):
    nest = {}
    for key, value in mapping_dict.items():
        category, subcategory = value
        if key in flat:
            if category not in nest:
                nest[category] = {}
            nest[category][subcategory] = flat[key]
        else:
            warn(f'key "{key}" not found in input "{flat}"')
    return nest


def validate_model_params(model_params):
    errors = {}
    for param_name, value in model_params.items():
        if value == '':
            errors[param_name] = False
        elif pd.isna(pd.to_datetime(value, format='%d/%m/%Y', errors='coerce')):
            errors[param_name] = 'Please enter a valid date in the format dd/mm/yyyy'
    all_dates = ['history_start', 'reference_start', 'reference_end', 'history_end', 'prediction_end']

    if errors:
        return errors
    # ...or if all the dates are valid, check that they're in the right order


def validate_costs(params):
    all_good = True  # //return a boolean as well so we dont have to loop thru to check if there are any errors

    subcats = ['Fostering (friend/relative)',
             'Fostering (in-house)',
             'Fostering (IFA)',
             'Residential (in-house)',
             'Residential (external)',
             'Supported',
             'Secure home',
             'Placed with family',
             'Other']
    if '' in params.values() or set(params.keys()) != set(subcats):
        all_good = False

    errors = {}
    for param_name, value in params.items():
        try:
            i = float(value)
            if i < 0:
                errors[param_name] = 'Please enter a positive number'
                all_good = False
        except ValueError:
            if value != '':
                errors[param_name] = 'Please enter a positive number'
                all_good = False
            else:
                errors[param_name] = False
    return all_good, errors

subcats = ['Fostering (friend/relative)',
             'Fostering (in-house)',
             'Fostering (IFA)',
             'Residential (in-house)',
             'Residential (external)',
             'Supported',
             'Secure home',
             'Placed with family',
             'Other']


def validate_proportions(props_dict):
    all_good = True  # //return a boolean as well so we dont have to loop thru to check if there are any errors

    if '' in props_dict.values() or set(props_dict.keys()) != set(subcats):
        all_good = False

    props_dict = props_dict.copy()
    errors = {}

    # if any values can't be cast to float, highlight those as errors
    # only if none are do we then check they add up to one

    witch = False  # does it float?
    for key, val in props_dict.items():
        witch = True
        try:
            props_dict[key] = float(val)
        except ValueError:
            witch = False
            if val != '':
                all_good = False
                errors[key] = 'Please enter a number between 0 and 1'
            else:
                errors[key] = False
        if witch:
            if not 0 <= props_dict[key] <= 1.000001:
                print(props_dict[key])
                all_good = False
                errors[key] = 'Please enter a number between 0 and 1'

    # get user to fix type errors first (?)
    if not witch or not all_good:
        return all_good, errors

    # check values for each category add up to 1
    props_nested = flat_to_nest(props_dict, cost_params_map)
    for key in props_nested:
        err_keys = [i for i in subcats if cost_params_map[i][0] == key][0:1]  # just show it on the first one

        category_vals = [float(n) for n in props_nested[key].values() if n.replace('.', '', 1).isdigit()]

        if abs(1 - sum(category_vals)) > 0.000001:
            print('~#~~~', key, ':::propssumto:::', sum(category_vals))
            result = f'Make sure the ratios for subcategories of "{key}" add up to exactly 1'
            all_good = False
        else:
            result = False
        for i in err_keys:
            errors[i] = result
    return all_good, errors
