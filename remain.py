from csdmpy.super_model import work_out_transition_rates, work_out_ingress_rates
import pandas as pd
import numpy as np
import os
from csdmpy import ingress

test_903_dir = os.path.join(os.path.dirname(__file__), 'csdmpy', 'tests', 'fake903_5yrs')
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

df = ingress.the_ingress_procedure(files_list)

print(df.columns)

cat_list = list(df['placement_type'].unique()) + ['Not in care']

print(cat_list)
n_trans, trans_rates = work_out_transition_rates(df, cat='Foster', start_date='01/01/2019', end_date='01/01/2020',
                                  cat_list=cat_list)


print(n_trans.to_string())
print(trans_rates.to_string())
pass

entrants = work_out_ingress_rates(df, cat='Foster', cat_list=cat_list, start_date='01/01/2019', end_date='01/01/2020',)

print(entrants)
print(':-)')
pass
