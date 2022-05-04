from csdmpy.super_model import get_daily_transition_rates, \
    get_daily_entrants, make_populations_ts, \
    transition_probs_per_bracket, the_model_itself
from csdmpy.config import age_brackets as bin_defs
from csdmpy.costs import calculate_costs
import pandas as pd
import numpy as np
import os
from csdmpy import ingress
import matplotlib.pyplot as pp
from csdmpy.utils import ezfiles

start, end, horizon = pd.to_datetime(['2019-06-01', '2021-01-01', '2035-01-01'])
step_size = '3m'

df = ingress.the_ingress_procedure(ezfiles())

past, future = the_model_itself(df, start, end, horizon, step_size)

print(past.to_string())

print(future.to_string())
#pp.plot(pd.concat([past, future]))



#pp.show()


p = pd.concat([past, future]).plot()
p.axvline(end, ls=':', c='g')
#
pp.show()
'''transitions_dict = transition_probs_per_bracket(df, bin_defs, start, end)
print('* * * * * Transition probabilities for each bin\n')
for bracket, t_mat in transitions_dict.items():
    print(str(bracket) + ':', t_mat, sep='\n')

pass
'''

##### COSTING STARTS HERE ###
df_dup = future.copy()
grouped_df = df_dup.groupby(level=1, axis=1).sum()

print('#'*70)
print(grouped_df)

base_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, },
                'Resi': {'in_house1':40, 'external':60},
                'Supported' : {'Sup': 40,},
                'Other': {'secure_home': 150, 'with_family':30, 'any_other':40}}
adjusted_costs = {'Foster': {'friend_relative': 100, 'in_house': 200, 'IFA': 300, },
                'Resi': {'in_house1':400, 'external':600},
                'Supported' : {'Sup': 400,},
                'Other': {'secure_home': 1500, 'with_family':30, 'any_other':400}}
cost_dict = {'base': base_costs, 'adjusted': adjusted_costs}

proportions = {'Foster': {'friend_relative': 0.5, 'in_house': 0.2, 'IFA': 0.3, },
                'Resi': {'in_house1':0.4, 'external':0.6},
                'Supported' : {'Sup': 1,},
                'Other': {'secure_home': 0.7, 'with_family':0.1, 'any_other':0.2}}

scenario_costs = calculate_costs(df_future=grouped_df, cost_dict= cost_dict, proportions=proportions, 
                                    step_size=step_size, inflation = True)
base_costs = scenario_costs['base']

print("#"*30)
print("COSTS HERE")
print(base_costs)
print("#"*30)