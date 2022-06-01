import pandas as np
import numpy as np
from csdmpy.super_model import *
# from ingress import ...
from csdmpy.costs import calculate_costs
from csdmpy.config import next_brackets


class Model:
    df = None
    # model_params
    start_date = None
    ref_start = None
    ref_end = None
    end_date = None
    horizon_date = None
    step_size = None
    bin_defs = None

    # stuff that will be calculated
    ts_info = None
    historic_pop = None
    future_pop = None
    adjusted_future_pop = None
    initial_pop = None
    
    age_out_ratios = None
    daily_probs = None
    step_probs = None
    entrant_rates = None
    past_costs = None
    future_costs = None

    def __init__(self, df=None, model_params=None, cost_params=None, adjustments=None):
        if df:
            self.df = df

        # assume everything coming in is valid param sets as they'll have been through check_params etc already
        if cost_params:
            self.cost_params = cost_params
        else:
            self.cost_params = None

        if adjustments:
            self.adjustments = adjustments
        else:
            self.adjustments = None

        if model_params:
            self.set_model_params(model_params)

    def do_everything(self):
        self.set_up_time_series()
        self.measure_system()
        self.predict()
        if self.cost_params:
            self.calculate_costs()

    def set_up_time_series(self):
        df, bin_defs, start_date, end_date, horizon_date, step_size \
            = self.df, self.bin_defs, self.start_date, self.end_date, self.horizon_date, self.step_size

        historic_pop = make_populations_ts(df, bin_defs, start_date, end_date, step_size).sort_index()
        ts_info = make_date_index(end_date, horizon_date, step_size, align_end=False).iloc[1:]
        future_pop = pd.DataFrame(columns=historic_pop.columns, index=ts_info.index)

        # - - - - - - - -- -  -- - - - -  - -  -  - - -
        print('* *][*][*] * * (( HISTORIC POPS ))\n')
        print(historic_pop.to_string())
        print('[[*]] *]] * * * * (( FUTURE POPS ))\n')
        print(future_pop.to_string())
        # - - - - - - - -- -  -- - - - -  - -  -  - - -

        initial_pop = historic_pop.loc[historic_pop.index.max()].copy()

        self.ts_info = ts_info
        self.historic_pop = historic_pop
        self.initial_pop = initial_pop
        self.future_pop = future_pop

        if self.adjustments:
            self.adjusted_future_pop = future_pop.copy()
        else:
            self.adjusted_future_pop = None

    def measure_system(self):
        df, bin_defs, start_date, end_date, ts_info = self.df, self.bin_defs, self.ref_start, self.ref_end, self.ts_info
        step_size = self.step_size
        
        age_out_ratios = ageing_probs_per_bracket(bin_defs, step_size)
        
        t_probs = transition_probs_per_bracket(df, bin_defs, start_date, end_date)

        # - - - - - - - -- -  -- - - - -  - -  -  - - -
        print('[[[*] * * * * (( TRANS PROBS ))\n')
        # - - - - - - - -- -  -- - - - -  - -  -  - - -


        for bracket, t_mat in t_probs.items():
            print(str(bracket) + ':', t_mat, sep='\n')

        precalced_transition_matrices = calculate_timestep_transition_matrices(ts_info, t_probs)
        
        entrance = daily_entrants_per_bracket(df, bin_defs, start_date, end_date)

        # - - - - - - - -- -  -- - - - -  - -  -  - - -
        print(f'[*]] * ****%%%(( ENTRANTS )) \n')
        for bracket, entrants_df in entrance.items():
            print(str(bracket) + ':', entrants_df, sep='\n')
        # - - - - - - - -- -  -- - - - -  - -  -  - - -

        print('')
        print(precalced_transition_matrices[max(precalced_transition_matrices)])
        
        self.age_out_ratios = age_out_ratios
        self.entrant_rates = entrance
        self.step_probs = precalced_transition_matrices

    def predict(self):
        df, ts_info, future_pop = self.df, self.ts_info, self.future_pop
        adjustments = self.adjustments
        
        if adjustments:
            adjusted_future_pop = self.adjusted_future_pop
        
        precalced_transition_matrices = self.step_probs
        entrant_rates = self.entrant_rates
        next_pop = self.initial_pop.copy()
        adj_next_pop = self.initial_pop.copy()

        for date in future_pop.index:
            step_days = ts_info.loc[date, 'step_days']
            print(f"* * * * * * * * {date} ")
            print('Making children older...')
            next_pop = apply_ageing(next_pop, {'fake': 'fake',
                                               'records': 'records'})
            if adjustments:
                adj_next_pop = apply_ageing(next_pop, {'fake': 'fake', 
                                                                'records': 'records'})
            print('Moving children around...')
            for age_bracket in next_pop.index.get_level_values('age_bin').unique():
                T = precalced_transition_matrices[step_days][age_bracket]
                next_pop[age_bracket] = T.dot(next_pop[age_bracket]) + entrant_rates[age_bracket] * step_days
                if adjustments:
                    adj_next_pop[age_bracket] = T.dot(adj_next_pop[age_bracket]) + entrant_rates[age_bracket] * step_days
                    adj_next_pop = apply_adjustments(adj_next_pop.copy(), adjustments)

            future_pop.loc[date] = next_pop
            if adjustments:
                adjusted_future_pop.loc[date] = adj_next_pop

        self.future_pop = future_pop  # now we can convert these to csv/whatever and send to the frontend
        if adjustments:
            self.adjusted_future_pop = adjusted_future_pop

    def calculate_costs(self):
        cost_params = self.cost_params
        future_costs = calculate_costs(self.future_pop, **cost_params)
        adjustments = self.adjustments
        if adjustments:
            adj_future_costs = calculate_costs(self.adjusted_future_pop, **cost_params)
        else:
            adj_future_costs = None

        past_cost_params = cost_params.copy()
        past_cost_params['inflation'] = None
        past_costs = calculate_costs(self.historic_pop, **cost_params)
        print(' = = = = #######################  = = = = ')
        print(type(past_costs))
        print(past_costs)
        self.past_costs = past_costs['base']
        self.future_costs = future_costs['base']

    def set_model_params(self, model_params):
        self.start_date = model_params['history_start']
        self.ref_start = model_params['reference_start']
        self.ref_end = model_params['reference_end']
        self.end_date = model_params['history_end']
        self.horizon_date = model_params['prediction_end']
        self.step_size = model_params['step_size']
        self.bin_defs = model_params['bin_defs']


    def update_cost_params(self, cost_params):
        self.cost_params = cost_params

    def gen_pop_graph(self, df, forecast_start_date):
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
            {'x': [forecast_start_date.strftime('%Y-%m-%d')] * 2,
             'y': [0, df.max().max()],
             'type': 'scatter',
             'line': {'dash': 'dot',
                      'width': 2},
             'mode': 'lines',
             'name': 'Forecast start'}
        )

        print('POP traces:', *tracey_beaker, sep='\n')
        return tracey_beaker

    @property
    def base_pop_graph(self):
        df = pd.concat([self.historic_pop, self.future_pop])
        forecast_start_date = self.end_date
        return self.gen_pop_graph(df, forecast_start_date)

    @property
    def adj_pop_graph(self):
        df = pd.concat([self.historic_pop, self.adjusted_future_pop])
        forecast_start_date = self.end_date
        return self.gen_pop_graph(df, forecast_start_date)


    @property
    def base_cost_graph(self):
        df = pd.concat([self.past_costs, self.future_costs])
        forecast_start_date = self.end_date
        return self.gen_cost_graph(df, forecast_start_date)
    @property
    def adj_cost_graph(self):
        df = pd.concat([self.past_costs, self.future_costs])
        forecast_start_date = self.end_date
        return self.gen_cost_graph(df, forecast_start_date)

    def gen_cost_graph(self, df, forecast_start_date):
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
            {'x': [self.end_date.strftime('%Y-%m-%d'), ] * 2,
             'y': [0, df.max().max()],
             'type': 'scatter',
             'line': {'dash': 'dot',
                      'width': 2},
             'mode': 'lines',
             'name': 'Forecast start'}
        )

        print('COST traces:', *tracey_beaker, sep='\n')
        return tracey_beaker

