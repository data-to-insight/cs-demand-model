from csdmpy.super_model import get_daily_transition_rates, \
    get_daily_entrants, make_populations_ts, \
    transition_probs_per_bracket, bin_defs, the_model_itself
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

start, end, horizon= pd.to_datetime(['2018-01-01', '2020-01-01', '2022-01-01'])
step_size = '1m'
transitions_dict = transition_probs_per_bracket(df, bin_defs, start, end)

for bracket, cats in bin_defs.items():
    print(str(bracket) + ':', cats, sep='  ')

print('* * * * * Transition probabilities for each bin\n')
for bracket, t_mat in transitions_dict.items():
    print(str(bracket) + ':', t_mat, sep='\n')

print('* * * * * Daily Entrants for each bin')

print('* * * * * Historical populations for each category')
print(make_populations_ts(df, bin_defs, start, end, step_size=step_size).to_string()) #TODO: fix this function...

print(df[['DECOM', 'DEC']].min(), df[['DECOM', 'DEC']].max())

the_model_itself(df, start, end, horizon, step_size)
