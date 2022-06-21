from csdmpy.classy import Model, ModelParams
from csdmpy.utils import ezfiles
from csdmpy.config import age_brackets as bin_defs
import pandas as pd
from csdmpy.api import ApiSession
from csdmpy.config import cost_params_map

step_size = '4'

hist_start, ref_start, ref_end, hist_end, pred_end = pd.to_datetime(
    ['2015-01-01', '2016-06-01', '2017-06-01', '2019-01-01', '2025-01-01'])

model_params = {}
model_params['history_start'] = hist_start
model_params['reference_start'] = ref_start
model_params['reference_end'] = ref_end
model_params['history_end'] = hist_end
model_params['prediction_end'] = pred_end
model_params['step_size'] = step_size
model_params['bin_defs'] = bin_defs
model_params = ModelParams(**model_params)

costs = {k: 100 for k in cost_params_map.keys()}
props = {k: 0.3 for k in cost_params_map.keys()}

session = ApiSession(ezfiles())

session.calculate_model(model_params, [])

session.calculate_costs(costs, props)

print('POPS =================')
print(session.model.future_pop.to_string())
print('================= COSTS')
print(session.model.future_costs.to_string())
