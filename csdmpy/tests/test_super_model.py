import pytest
import pandas as pd

from csdmpy.super_model import get_daily_entrants, get_daily_transition_rates, step_to_days, transition_probs_per_bracket, daily_entrants_per_bracket, ageing_probs_per_bracket

def test_get_daily_entrants(dummy_entrant_eps):
    cat_list = ('Foster', 'Resi', 'Supported', 'Other')
    daily_entrants =  get_daily_entrants(df=dummy_entrant_eps, cat_list=cat_list)
    # check that all generated values are valid
    assert (daily_entrants.values <= 1).all()
    # check individual values
    assert daily_entrants['Supported'] == 0.25
    assert daily_entrants['Other'] == 0.00
    # That is, 1 supported and 2 foster children came into care over 4 days, as seen from the data.

def test_get_daily_transition_rates(dummy_entrant_eps):
    transition_rates = get_daily_transition_rates(df=dummy_entrant_eps)
    # check that all rates generated are fractions
    assert (transition_rates.values <= 1).all()
    # check that the imputed values for staying in the same placement are the same for each category
    assert transition_rates.loc['Foster', 'Foster'] == transition_rates.loc['Resi', 'Resi']
    # check values
    assert transition_rates.loc['Resi', 'Foster'].round(decimals=3) == 0.028
    assert transition_rates.loc['Foster', 'Resi'].round(decimals=3) == 0.083

def test_step_to_days():
    days = step_to_days(step_size='7m')
    assert days == 210

    days = step_to_days(step_size='5d')
    assert days == 5

def test_transition_probs_per_bracket(dummy_entrant_eps, dummy_age_brackets):
    tran_probs = transition_probs_per_bracket(df=dummy_entrant_eps, bin_defs=dummy_age_brackets, start_date='18/05/2000', end_date='22/05/2000')
    # Check that a dictionary of DataFrames is generated.
    assert isinstance(tran_probs, dict)
    assert isinstance(tran_probs['10 to 16'], pd.DataFrame)

    # Check values.
    dfa = tran_probs['16 to 18']
    assert dfa.loc['Supported', 'Foster'].round(decimals=3) == 0.167
    assert dfa.loc[:, 'Foster'].round(decimals=3).tolist() == [0.833, 0.0, 0.167]

def test_daily_entrants_per_bracket(dummy_entrant_eps, dummy_age_brackets):
    ent_probs = daily_entrants_per_bracket(df=dummy_entrant_eps, bin_defs=dummy_age_brackets, start_date='18/05/2000', end_date='22/05/2000')
    # check values calculated.
    dfa = ent_probs['16 to 18']
    assert ent_probs['16 to 18']['Foster'] == 0.25
    # check data structure generated.
    assert isinstance(ent_probs, dict)
    assert ent_probs.keys() == dummy_age_brackets.keys()

def test_ageing_probs_per_bracket(dummy_age_brackets):
    aging_matrix = ageing_probs_per_bracket(dummy_age_brackets, step_size='3m')
    # check data structure
    assert isinstance(aging_matrix, dict)
    # check values
    assert round(aging_matrix['1 to 5'], 3) == 0.062

    aging_matrix = ageing_probs_per_bracket(dummy_age_brackets, step_size='4d')
    assert round(aging_matrix['1 to 5'], 3) == 0.003

def calculate_timestep_transition_matrices(dummy_entrant_eps, dummy_age_brackets):
    ts_info = make_date_index(start_date='22/05/2000', end_date='01/08/2003', step='5w')
    daily_t_probs = transition_probs_per_bracket(df=dummy_entrant_eps, bin_defs=dummy_age_brackets, start_date='18/05/2000', end_date='22/05/2000')
    result = calculate_timestep_transition_matrices(ts_info, daily_t_probs)
    # check data structure generated.
    assert isinstance(result, dict)
    # first and second outer layers should be dictionaries.
    assert isinstance(result[1], dict)
    # third layer in should be a DataFrame.
    assert isinstance(result[35]['16 to 18'], pd.DataFrame())

    # check values generated
    assert result[35]['16 to 18'].loc['Supported'].round(decimals=4).tolist() == [0.0119, 0.0, 0.0017]
