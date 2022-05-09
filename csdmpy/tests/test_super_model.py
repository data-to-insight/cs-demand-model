import pytest
import pandas as pd

from csdmpy.super_model import get_daily_entrants, get_daily_transition_rates, step_to_days

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