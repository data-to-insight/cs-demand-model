import pytest
import pandas as pd

from csdmpy.utils import truncate


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
