from pathlib import Path

import pandas as pd
from .config import ACCEPTED_DATE_FORMATS, cost_params_map
import os
from warnings import warn

test_903_dir = Path(__file__).parent / 'xxx' / 'fake903_5yrs'

def ezsesh():
    from csdmpy.classy import Model, ModelParams
    from csdmpy.utils import ezfiles
    from csdmpy.config import age_brackets as bin_defs
    import pandas as pd
    import matplotlib.pyplot as pp

    from csdmpy.api import ApiSession
    from csdmpy.config import cost_params_map

    step_size = '4'

    hist_start, ref_start, ref_end, hist_end, pred_end = pd.to_datetime(
        ['2015-01-01', '2016-06-01', '2017-06-01', '2019-01-01', '2021-01-01'])

    model_params = {}
    model_params['history_start'] = hist_start
    model_params['reference_start'] = ref_start
    model_params['reference_end'] = ref_end
    model_params['history_end'] = hist_end
    model_params['prediction_end'] = pred_end
    model_params['step_size'] = step_size
    model_params['bin_defs'] = bin_defs
    model_params = ModelParams(**model_params)

    costs = {k: '100' for k in cost_params_map.keys()}
    props = {k: '0.3' for k in cost_params_map.keys()}

    session = ApiSession(ezfiles())

    session.calculate_model(model_params, [])

    session.calculate_costs(costs, props, None)
    return session


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


def deviation_bounds(data, variance_values):
    """ This function adds and subtracts 1 standard deviation to calculate the uppper and lower bounds, respectively, of data provided to it.  """

    # standard deviation = square_root(variances)
    standard_deviations = variance_values.apply(lambda x : x**0.5)
    
    upper_values = data.copy()
    lower_values = data.copy()
    upper_values = upper_values + standard_deviations
    lower_values = lower_values - standard_deviations

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


def apdd(df, ab=None, pt=None, decom=None, dec=None):
    mask = pd.Series(True, index=df.index)
    if ab:
        mask *= df['age_bin'] == ab
    if pt:
        mask *= df['placement_type'] == pt
    if decom:
        mask *= df['DECOM'] == decom
    if dec:
        mask *= df['DEC'] == dec
    return df[mask]
