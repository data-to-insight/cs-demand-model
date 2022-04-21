import pandas as pd
import pytest
from csdmpy import ingress

"""
fake_df1
3 children with 2 days in Foster care each
1 goes to 2 days in Resi, ; goes to 2 days in Supp; 1 leaves care
expected transition probs: 
F -> R: 1/6
F -> S: 1/6
F -> F: 3/6
S/R -> F/S/R: all 0
"""
@pytest.fixture(scope='session')
dummy_df = pd.DataFrame([
    {'CHILD': 111, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U1', 'DOB': '10/05/1983'}, # foster
    {'CHILD': 111, 'DECOM': '20/05/2000', 'DEC': '22/01/2001', 'PLACE': 'K2', 'DOB': '10/05/1983'}, # resi
 ,
    {'CHILD': 222, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U1', 'DOB': '10/05/1983'}, # foster
 ,
    {'CHILD': 333, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U2', 'DOB': '10/05/1983'}, # foster
    {'CHILD': 333, 'DECOM': '20/05/2000', 'DEC': '22/05/2000', 'PLACE': 'H5', 'DOB': '10/05/1983'}, # supported

])

"""
fake_df2
3 children who change their placement types within a 10-day period. 
16/05/2000 - 26/05/2000
"""
fake_df2 = pd.DataFrame([
    {'CHILD': 111, 'DECOM': '16/05/2000', 'DEC':'20/05/2000', 'PLACE': 'U1'}, # FOSTER
    {'CHILD': 111, 'DECOM': '20/05/2000', 'DEC':'22/01/2001', 'PLACE': 'K2'}, # RESI

    {'CHILD': 222, 'DECOM': '17/05/2000', 'DEC':'19/05/2000', 'PLACE': 'R1'}, # resi
    {'CHILD': 222, 'DECOM': '19/05/2000', 'DEC':'30/01/2001', 'PLACE': 'XX'}, # outside

    {'CHILD': 333, 'DECOM': '18/05/2000', 'DEC':'20/05/2000', 'PLACE': 'XX'}, # outside
    {'CHILD': 333, 'DECOM': '21/05/2000', 'DEC':'24/05/2000', 'PLACE': 'H5'}, # supported

])

"""
possible movements that can be modelled
- leaves care
- enters into care
- ages up in the same placement
- moves to a new placement type.
"""

fake_trans_dict = {(-1, 1): {'Foster': 1.0},
                   (1, 5): {'Foster': 1.8},
                   (5, 10): {'Foster': 0.1, 'Resi': 0.5},
                   (10, 16): {'Foster': 0.8, 'Resi': 1.5},
                   (16, 18): {'Foster': 0.6, 'Resi': 0.5, 'Supported': 1.8}}

fake_entrants_dict = {(-1, 1): {'Foster': 1.0},
                      (1, 5): {'Foster': 1.8},
                      (5, 10): {'Foster': 0.1, 'Resi': 0.5},
                      (10, 16): {'Foster': 0.8, 'Resi': 1.5},
                      (16, 18): {'Foster': 0.6, 'Resi': 0.5, 'Supported': 1.8}}

fake_ageing_probs = {(-1, 1): 0.20,
                     (1, 5): 0.63,
                     (5, 10): 0.50,
                     (10, 16): 0.79,
                     (16, 18): 0.48}