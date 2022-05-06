import pytest
import pandas as pd

from csdmpy.super_model import get_daily_entrants

def test_get_daily_entrants(dummy_entrant_eps):
    cat_list = ('Foster', 'Resi', 'Supported', 'Other')
    daily_entrants =  get_daily_entrants(df=dummy_entrant_eps, cat_list=cat_list)
    # check that all generated values are valid
    assert (daily_entrants.values <= 1).all()
    # check individual values
    assert daily_entrants['Supported'] == 0.25
    assert daily_entrants['Other'] == 0.00
    # That is, 1 supported and 2 foster children came into care over 4 days, as seen from the data.
