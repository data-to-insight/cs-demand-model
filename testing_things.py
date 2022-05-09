import pandas as pd
from csdmpy.super_model import get_daily_entrants, get_daily_transition_rates

def dummy_entrant_eps():
    df = pd.DataFrame([
        {'CHILD': 111, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U1', 'DOB': '10/05/1983', 'placement_type': 'Foster', 'placement_type_before':'Foster', 'placement_type_after':'Not in care',},  # foster
        {'CHILD': 111, 'DECOM': '20/05/2000', 'DEC': '22/05/2000', 'PLACE': 'K2', 'DOB': '10/05/1983', 'placement_type': 'Resi', 'placement_type_before':'Foster', 'placement_type_after':'Not in care',},  # resi

        {'CHILD': 222, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U1', 'DOB': '10/05/1983', 'placement_type': 'Foster', 'placement_type_before':'Not in care', 'placement_type_after':'Not in care',},  # foster

        {'CHILD': 333, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U2', 'DOB': '10/05/1983', 'placement_type': 'Foster', 'placement_type_before':'Not in care', 'placement_type_after':'Not in care',},  # foster
        {'CHILD': 333, 'DECOM': '20/05/2000', 'DEC': '22/05/2000', 'PLACE': 'H5', 'DOB': '10/05/1983', 'placement_type': 'Supported', 'placement_type_before':'Foster', 'placement_type_after':'Not in care',},  # supported

        {'CHILD': 222, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'H5', 'DOB': '10/05/1983', 'placement_type': 'Supported', 'placement_type_before':'Not in care', 'placement_type_after':'Not in care',},  # supported
    ])
    for col in ['DECOM', 'DEC', 'DOB']:
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y')
    return df
def dummy_entrant_eps():
    df = pd.DataFrame([
        {'CHILD': 111, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U1', 'DOB': '10/05/1983', 'placement_type': 'Foster', 'placement_type_before':'Foster', 'placement_type_after':'Resi',},  # foster
        {'CHILD': 111, 'DECOM': '20/05/2000', 'DEC': '22/05/2000', 'PLACE': 'K2', 'DOB': '10/05/1983', 'placement_type': 'Resi', 'placement_type_before':'Foster', 'placement_type_after':'Foster',},  # resi

        {'CHILD': 222, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U1', 'DOB': '10/05/1983', 'placement_type': 'Foster', 'placement_type_before':'Not in care', 'placement_type_after':'Not in care',},  # foster

        {'CHILD': 333, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'U2', 'DOB': '10/05/1983', 'placement_type': 'Foster', 'placement_type_before':'Not in care', 'placement_type_after':'Supported',},  # foster
        {'CHILD': 333, 'DECOM': '20/05/2000', 'DEC': '22/05/2000', 'PLACE': 'H5', 'DOB': '10/05/1983', 'placement_type': 'Supported', 'placement_type_before':'Foster', 'placement_type_after':'Not in care',},  # supported

        {'CHILD': 444, 'DECOM': '18/05/2000', 'DEC': '20/05/2000', 'PLACE': 'H5', 'DOB': '10/05/1983', 'placement_type': 'Supported', 'placement_type_before':'Not in care', 'placement_type_after':'Not in care',},  # supported
    ])
    for col in ['DECOM', 'DEC', 'DOB']:
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y')
    return df

# what's the structure of df
df = dummy_entrant_eps()
# what's the structure of cat_list
cat_list = ('Foster', 'Resi', 'Supported', 'Other')

daily_entrants =  get_daily_transition_rates(df=df)
type(daily_entrants)
print((daily_entrants.values <1).all())
print(daily_entrants)