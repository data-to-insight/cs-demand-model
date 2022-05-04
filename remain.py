from csdmpy.super_model import get_daily_transition_rates, \
    get_daily_entrants, make_populations_ts, \
    transition_probs_per_bracket, bin_defs, the_model_itself
from csdmpy.utils import ezfiles
import pandas as pd
import numpy as np
import os
from csdmpy import ingress


files_list = ezfiles()

df = ingress.the_ingress_procedure(files_list)

start, end, horizon= pd.to_datetime(['2018-01-01', '2020-01-01', '2022-01-01'])
step_size = '6m'

for bracket, cats in bin_defs.items():
    print(str(bracket) + ':', cats, sep='  ')

transitions_dict = transition_probs_per_bracket(df, bin_defs, start, end)
print('* * * * * Transition probabilities for each bin\n')
for bracket, t_mat in transitions_dict.items():
    print(str(bracket) + ':', t_mat, sep='\n')

print('* * * * * Daily Entrants for each bin')

print('* * * * * Historical populations for each category')
print(make_populations_ts(df, bin_defs, start, end, step_size=step_size).to_string()) #TODO: fix this function...

print(df[['DECOM', 'DEC']].min(), df[['DECOM', 'DEC']].max())

the_model_itself(df, start, end, horizon, step_size)
