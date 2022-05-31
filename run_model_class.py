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

model = Model(df, start, end, horizon, step_size, bin_defs, cost_params)

model.do_everything()

print(model.step_probs.keys())

all_pops = pd.concat([model.historic_pop, model.future_pop])
print(all_pops.to_string())

print(model.upper_pop.to_string())
print("*"*100)
print(model.lower_pop.to_string())

costs = calculate_costs(df_future=model.future_pop, cost_dict=cost_dict, proportions=proportions, step_size=step_size, inflation=None)
print('#'*80)
print(costs)

p = all_pops.plot()
p.axvline(end, ls=":", c="g")

pp.show()
