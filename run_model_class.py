from csdmpy.classy import Model
from csdmpy.utils import ezfiles, cost_translation
from csdmpy.config import cost_params_map
from csdmpy.config import age_brackets as bin_defs
from csdmpy.ingress import the_ingress_procedure
from csdmpy.costs import calculate_costs
import matplotlib.pyplot as pp
import pandas as pd

flat_costs = {
    'Fostering (friend/relative)': 10,
    'Fostering (in-house)': 20,
    'Fostering (IFA)': 50,
    'Residential (in-house)': 60,
    'Residential (external)': 70,
    'Supported': 80,
    'Other (secure-home)': 30,
    'Other (placed-with-family)': 40,
    'Other (other)': 90
}

flat_proportions = {
    'Fostering (friend/relative)': 0.5,
    'Fostering (in-house)': 0.2,
    'Fostering (IFA)': 0.3,
    'Residential (in-house)': 0.4,
    'Residential (external)': 0.6,
    'Supported': 1,
    'Other (secure-home)': 0.2,
    'Other (placed-with-family)': 0.3,
    'Other (other)': 0.5
}

cost_dict, proportions = cost_translation(flat_costs, flat_proportions, cost_params_map)

start, end, horizon = pd.to_datetime(["2019-01-01", "2020-01-01", "2025-01-01"])
step_size = "4m"

cost_params = {
    "cost_dict": cost_dict,
    "proportions": proportions,
    "inflation": 0.2,
    "step_size": step_size,
}

df = the_ingress_procedure(ezfiles())

base_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, },
              'Resi': {'in_house1': 40, 'external': 60},
              'Supported': {'Sup': 40, },
              'Other': {'secure_home': 150, 'with_family': 30, 'any_other': 40}}

cost_dict = {'base': base_costs} #, 'adjusted': adjusted_costs}

proportions = {'Foster': {'friend_relative': 0.5, 'in_house': 0.2, 'IFA': 0.3, },
               'Resi': {'in_house1': 0.4, 'external': 0.6},
               'Supported': {'Sup': 1, },
               'Other': {'secure_home': 0.7, 'with_family': 0.1, 'any_other': 0.2}}

hist_start, ref_start, ref_end, hist_end, pred_end = pd.to_datetime(
    ['2015-01-01', '2016-06-01', '2017-06-01', '2019-01-01', '2025-01-01'])

step_size = '4m'
model_params = {}
model_params['history_start'] = hist_start
model_params['reference_start'] = ref_start
model_params['reference_end'] = ref_end
model_params['history_end'] = hist_end
model_params['prediction_end'] = pred_end
model_params['step_size'] = step_size
model_params['bin_defs'] = bin_defs
model_params = ModelParams(**model_params)


adjustments = [{'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Resi', 'n': 0, 'id': 100},
               {'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Other', 'n': 10, 'id': 101}]

print(df.columns)
model = Model(df, model_params=model_params, adjustments=adjustments)

cost_params = {'cost_dict': cost_dict,
               'proportions': proportions,
               'inflation': 0.2,
               'step_size': step_size}
model.calculate_costs(cost_params)

print(model.step_probs.keys())

all_pops = pd.concat([model.historic_pop, model.future_pop])
adj_pops = pd.concat([model.historic_pop, model.adjusted_future_pop])

print(all_pops.to_string())

print("VARIANCEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEES")
print(model.variances)
print('********************* upper pop ****************************')
print(model.upper_pop)
print('********************* lower pop ****************************')
print(model.lower_pop)

costs = calculate_costs(df_future=model.future_pop, cost_dict=cost_dict, proportions=proportions, step_size=step_size, inflation=None)
print('#'*80)
print(costs)

p = all_pops.plot()
p.axvline(end, ls=":", c="g")
fig, axe = pp.subplots(2, figsize=[15, 9])
axe[0].set_title('base pops')
axe[0].plot(all_pops, marker='+')
axe[0].legend(all_pops.columns)
axe[0].axvline(hist_end, ls=':', c='g')
axe[0].axvspan(ref_start, ref_end, color='y', alpha=0.3)

axe[1].set_title('adjusted pops')
axe[1].plot(adj_pops,marker='x')
axe[1].axvline(hist_end, ls=':', c='g')
axe[1].axvspan(ref_start, ref_end, color='y', alpha=0.3)

fig.set_tight_layout(tight=True)
pp.show()

#adjustments = [{'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Resi', 'n': 0, 'id': 100},
#               {'age_bracket': '10 to 16', 'from': 'Resi', 'to': 'Other', 'n': 3, 'id': 101}]


pass

