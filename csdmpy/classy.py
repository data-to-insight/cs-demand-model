import pandas as np
import numpy as np
from csdmpy.super_model import *
# from ingress import ...
from csdmpy.costs import calculate_costs


class Model:
    def __init__(self, df, model_params, cost_params=None, adjustments=None):
        self.df = df

        self.start_date = model_params['history_start']
        self.ref_start = model_params['reference_start']
        self.ref_end = model_params['reference_end']
        self.end_date = model_params['history_end']
        self.horizon_date = model_params['prediction_end']
        self.step_size = model_params['step_size']
        self.bin_defs = model_params['bin_defs']

        self.ts_info = None
        self.historic_pop = None
        self.future_pop = None
        self.initial_pop = None

        self.daily_probs = None
        self.step_probs = None
        self.entrant_rates = None

        if cost_params:
            self.cost_params = cost_params
            self.need_to_calculate_costs = True
        else:
            self.cost_params = None
            self.need_to_calculate_costs = False

        self.need_to_run_model = True  # if params are updated

    def do_everything(self):
        self.set_up_time_series()
        self.measure_system()
        self.predict()
        if self.cost_params:
            self.calculate_costs()
        self.need_to_run_model = False

    def set_up_time_series(self):
        df, bin_defs, start_date, end_date, horizon_date, step_size \
            = self.df, self.bin_defs, self.start_date, self.end_date, self.horizon_date, self.step_size

        historic_pop = make_populations_ts(df, bin_defs, start_date, end_date, step_size).sort_index()
        ts_info = make_date_index(end_date, horizon_date, step_size, align_end=False).iloc[1:]
        future_pop = pd.DataFrame(columns=historic_pop.columns, index=ts_info.index)

        print('* *][*][*] * * (( HISTORIC POPS ))\n')
        print(historic_pop.to_string())
        print('[[*]] *]] * * * * (( FUTURE POPS ))\n')
        print(future_pop.to_string())
        initial_pop = historic_pop.loc[historic_pop.index.max()].copy()

        self.ts_info = ts_info
        self.historic_pop = historic_pop
        self.initial_pop = initial_pop
        self.future_pop = future_pop

        self.past_costs = None
        self.future_costs = None

    def measure_system(self):
        df, bin_defs, start_date, end_date, ts_info = self.df, self.bin_defs, self.ref_start, self.ref_end, self.ts_info

        t_probs = transition_probs_per_bracket(df, bin_defs, start_date, end_date)

        print("[[[*] * * * * (( TRANS PROBS ))\n")

        for bracket, t_mat in t_probs.items():
            print(str(bracket) + ':', t_mat, sep='\n')

        precalced_transition_matrices = calculate_timestep_transition_matrices(ts_info, t_probs)

        entrance = daily_entrants_per_bracket(df, bin_defs, start_date, end_date)

        print(f"[*]] * ****%%%(( ENTRANTS )) \n")
        for bracket, entrants_df in entrance.items():
            print(str(bracket) + ":", entrants_df, sep="\n")
        print(precalced_transition_matrices[max(precalced_transition_matrices)])

        self.entrant_rates = entrance
        self.step_probs = precalced_transition_matrices

    def predict(self):
        df, ts_info, future_pop = self.df, self.ts_info, self.future_pop

        precalced_transition_matrices = self.step_probs
        entrant_rates = self.entrant_rates
        next_pop = self.initial_pop

        for date in future_pop.index:
            step_days = ts_info.loc[date, 'step_days']
            print(f"* * * * * * * * {date} ")
            print('Making children older...')
            next_pop = apply_ageing(next_pop, {'fake': 'fake',
                                               'records': 'records'})
            print('Moving children around...')
            for age_bracket in next_pop.index.get_level_values('age_bin').unique():
                T = precalced_transition_matrices[step_days][age_bracket]
                next_pop[age_bracket] = T.dot(next_pop[age_bracket]) + entrant_rates[age_bracket] * step_days

            future_pop.loc[date] = next_pop

        self.future_pop = future_pop  # now we can convert these to csv/whatever and send to the frontend

    def calculate_costs(self):
        cost_params = self.cost_params
        future_costs = calculate_costs(self.future_pop, **cost_params)
        past_cost_params = cost_params.copy()
        past_cost_params["inflation"] = None
        past_costs = calculate_costs(self.historic_pop, **cost_params)
        print(' = = = = #######################  = = = = ')
        print(type(past_costs))
        print(past_costs)
        self.past_costs = past_costs['base']
        self.future_costs = future_costs['base']

    def update_params(self, params):
        self.__init__(**params)

    def update_cost_params(self, cost_params):
        self.cost_params.update(cost_params)
        self.need_to_calculate_costs = True

    @property
    def pop_graphs(self):
        df = pd.concat([self.historic_pop, self.future_pop])
        forecast_start_date = self.end_date

        # fragile container of trace objects to be drawn by plotly.js
        tracey_beaker = [
            {
                'x': df.index.strftime('%Y-%m-%d').to_list(),
                'y': df[col].fillna(-1).to_list(),
                'type': 'scatter',
                'name': ' - '.join(col)
             } for col in df
        ]

        # noinspection PyTypeChecker
        tracey_beaker.append(
            {'x': [self.end_date.strftime('%Y-%m-%d')] * 2,
             'y': [0, df.max().max()],
             'type': 'scatter',
             'line': {'dash': 'dot',
                      'width': 2},
             'mode': 'lines',
             'name': 'Forecast start'}
        )

        print('tracey:', *tracey_beaker)
        return tracey_beaker

    @property
    def cost_graphs(self):
        df = pd.concat([self.past_costs, self.future_costs])
        forecast_start_date = self.end_date

        # fragile container of trace objects to be drawn by plotly.js
        tracey_beaker = [
            {
                'x': df.index.strftime('%Y-%m-%d').to_list(),
                'y': df[col].fillna(-1).to_list(),
                'type': 'scatter',
                'name': ' - '.join(col)
             } for col in df
        ]

        tracey_beaker.append(
            {'x': [self.end_date.strftime('%Y-%m-%d'), ] * 2,
             'y': [0, df.max().max()],
             'type': 'scatter',
             'line': {'dash': 'dot',
                      'width': 2},
             'mode': 'lines',
             'name': 'Forecast start'}
        )

        print('tracey:', *tracey_beaker)
        return tracey_beaker

