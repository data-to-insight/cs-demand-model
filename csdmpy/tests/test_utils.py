import pytest
import pandas as pd

from csdmpy.utils import truncate, get_ongoing, split_age_bin


def test_truncate(dummy_data_5_eps):
    print('\n * * * * input\n')
    print(dummy_data_5_eps)

    start, end = pd.to_datetime(('10/05/2000', '19/05/2000'), format='%d/%m/%Y')
    result = truncate(dummy_data_5_eps, start, end)
    print(f'* * * * \n, {start}, {end}')
    print(result.to_string())
    assert result['DECOM'].to_list() == pd.to_datetime(['2000-05-18'] * 3).to_list()

    start, end = pd.to_datetime(('20/05/2000', '21/05/2000'), format='%d/%m/%Y')
    result = truncate(dummy_data_5_eps, start, end, clip=True)
    print(f'* * * * \n, {start}, {end}')
    print(result.to_string())
    assert result['DECOM'].to_list() == pd.to_datetime(['2000-05-20'] * 2).to_list()
    assert result['DEC'].to_list() == pd.to_datetime(['2000-05-21'] * 2).to_list()

def test_get_ongoing(dummy_data_5_eps):
    
    start, end = pd.to_datetime(('20/05/2000', '21/05/2000'), format='%d/%m/%Y')

    t1 = '20/05/2022'
    df = get_ongoing(df, t1, s_col='DECOM', e_col='DEC')
    # if it ended before that time, ended at that time, or started after that time, then it is not ongoing.
    # check that the only episodes that remain are ongoing episodes.
    condition = (df[e_col]<t) | (df[e_col]==t) | (df[s_col]>t)
    result = len(df[condition])
    assert result == 0
    assert df['DEC'].to_list() == pd.to_datetime(['2000-05-22'] * 2).to_list()
    assert df['DEC'].to_list() == pd.to_datetime(['2000-05-20'] * 2).to_list()

    t2 = '23/05/2022'
    df = get_ongoing(df, t2, s_col='DECOM', e_col='DEC')
    assert len(df) == 0

    def test_split_age_bin():
        assert 5, 10 == split_age_bin('5 to 10')
        assert -1, 1 == split_age_bin('-1 to 1.0')