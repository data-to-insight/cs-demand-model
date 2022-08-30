from csdmpy.classy import Model, ModelParams
from csdmpy.utils import ezfiles
from csdmpy.config import age_brackets as bin_defs
import pandas as pd
import matplotlib.pyplot as pp

from csdmpy.api import ApiSession
from csdmpy.config import cost_params_map

step_size = '1d'

hist_start, ref_start, ref_end, hist_end, pred_end = pd.to_datetime(
    ['2015-01-01', '2019-07-01', '2020-01-01', '2020-01-01', '2021-07-01'])

model_params = {}
model_params['history_start'] = hist_start
model_params['reference_start'] = ref_start
model_params['reference_end'] = ref_end
model_params['history_end'] = hist_end
model_params['prediction_end'] = pred_end
model_params['step_size'] = step_size
model_params['bin_defs'] = bin_defs
model_params = ModelParams(**model_params)

costs = {k: '100' for k in cost_params_map.keys()}
props = {k: '0.3' for k in cost_params_map.keys()}

session = ApiSession(ezfiles())

session.calculate_model(model_params, [])

session.calculate_costs(costs, props, None)
print('----------------')
session.model.print_everything()

pd.concat([session.model.historic_pop, session.model.future_pop], axis=0).plot()
pp.axvline(hist_end, alpha=0.4)
pp.axvspan(ref_start, ref_end, alpha=0.1)
pp.show()

'''print('POPS =================')
print(session.model.future_pop.to_string())
print('================= COSTS')
print(session.model.future_costs.to_string())
all_pops = pd.concat([session.model.historic_pop, session.model.future_pop])

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

'''