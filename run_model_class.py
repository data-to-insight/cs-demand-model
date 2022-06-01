from csdmpy.classy import Model
from csdmpy.utils import ezfiles
from csdmpy.config import age_brackets as bin_defs
from csdmpy.ingress import the_ingress_procedure
import matplotlib.pyplot as pp
import pandas as pd

base_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, },
              'Resi': {'in_house1': 40, 'external': 60},
              'Supported': {'Sup': 40, },
              'Other': {'secure_home': 150, 'with_family': 30, 'any_other': 40}}

adjusted_costs = {'Foster': {'friend_relative': 100, 'in_house': 200, 'IFA': 300, },
                  'Resi': {'in_house1': 400, 'external': 600},
                  'Supported': {'Sup': 400, },
                  'Other': {'secure_home': 1500, 'with_family': 30, 'any_other': 400}}

cost_dict = {'base': base_costs} #, 'adjusted': adjusted_costs}

proportions = {'Foster': {'friend_relative': 0.5, 'in_house': 0.2, 'IFA': 0.3, },
               'Resi': {'in_house1': 0.4, 'external': 0.6},
               'Supported': {'Sup': 1, },
               'Other': {'secure_home': 0.7, 'with_family': 0.1, 'any_other': 0.2}}

hist_start, ref_start, ref_end, hist_end, pred_end = pd.to_datetime(
    ['2015-01-01', '2016-01-01', '2017-01-01', '2019-01-01', '2025-01-01'])

step_size = '4m'

bin_defs = {'10 to 16': ('Foster', 'Resi', 'Other'), }

cost_params = {'cost_dict': cost_dict,
               'proportions': proportions,
               'inflation': 0.2,
               'step_size': step_size}

df = the_ingress_procedure(ezfiles())

adjustments = [{'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Resi', 'n': 0, 'id': 100},
               {'age_bracket': '10 to 16', 'from': 'Resi', 'to': 'Other', 'n': 3, 'id': 101}]

model_params = {}
model_params['history_start'] = hist_start
model_params['reference_start'] = ref_start
model_params['reference_end'] = ref_end
model_params['history_end'] = hist_end
model_params['prediction_end'] = pred_end
model_params['step_size'] = step_size
model_params['bin_defs'] = bin_defs

print(df.columns)
model = Model(df)

model.set_model_params(model_params)
model.cost_params = cost_params
model.adjustments = adjustments

model.do_everything()

print(model.step_probs.keys())

all_pops = pd.concat([model.historic_pop, model.future_pop])
adj_pops = pd.concat([model.historic_pop, model.adjusted_future_pop])

print(all_pops.to_string())

p = pd.concat((all_pops,)).plot()
p.axvline(hist_end, ls=':', c='g')

p.axvspan(ref_start, ref_end, color='y', alpha=0.3)

pp.show()

adjustments = [{'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Resi', 'n': 0, 'id': 100},
               {'age_bracket': '10 to 16', 'from': 'Resi', 'to': 'Other', 'n': 3, 'id': 101}]


pass

