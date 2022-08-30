from dataclasses import field

import pandas as pd
from marshmallow_dataclass import dataclass
from datetime import date
from typing import Mapping, Any

from csdmpy.config import age_brackets
from csdmpy.super_model import *  # ...
from csdmpy.costs import calculate_costs
from csdmpy.utils import deviation_bounds


@dataclass(frozen=True)
class ModelParams:
    history_start: date
    reference_start: date
    reference_end: date
    history_end: date
    prediction_end: date
    step_size: str = '1d'
    bin_defs: Mapping[str, Any] = field(default_factory=lambda: age_brackets)


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
    adjusted_future_costs = None
    _default_proportions = None

    def __init__(self, df=None, model_params: ModelParams = None, adjustments=None):
        print('>> * >> * >> INITIALISING MODEL INISTANCE')
        print('>>> MODEL PARAMS:\n', model_params)
        print('>>> ADJUSTMENTS:\n', adjustments)
        self.df = df

        self.start_date = model_params.history_start
        self.ref_start = model_params.reference_start
        self.ref_end = model_params.reference_end
        self.end_date = model_params.history_end
        self.horizon_date = model_params.prediction_end
        self.step_size =  model_params.step_size #f'{model_params.step_size}m'
        self.bin_defs = model_params.bin_defs

        self.adjustments = adjustments

        self.set_up_time_series()
        self.measure_system()
        self.predict()

    def set_up_time_series(self):
        df, bin_defs, start_date, end_date, horizon_date, step_size \
            = self.df, self.bin_defs, self.start_date, self.end_date, self.horizon_date, self.step_size

        historic_pop = make_populations_ts(df, bin_defs, start_date, end_date, step_size).sort_index()
        ts_info = make_date_index(end_date, horizon_date, step_size, align_end=False).iloc[1:]
        future_pop = pd.DataFrame(columns=historic_pop.columns, index=ts_info.index)
        print('>> * >> * >> SETTING UP TIME SERIES')
        # - - - - - - - -- -  -- - - - -  - -  -  - - -
        print('>>> HISTORIC POPS:\n')
        print(historic_pop.to_string())
        print('>>> FUTURE TIMESTAMPS:\n')
        print(', '.join(str(i) for i in future_pop.index))
        # - - - - - - - -- -  -- - - - -  - -  -  - - -
        #historic_pop.loc[historic_pop.index.max(), :] = 100

        initial_pop = historic_pop.loc[historic_pop.index.max()].copy().astype(float)
        self.ts_info = ts_info
        self.historic_pop = historic_pop
        self.initial_pop = initial_pop
        self.future_pop = future_pop

        if self.adjustments:
            self.adjusted_future_pop = future_pop.copy()
        else:
            self.adjusted_future_pop = None

    def measure_system(self):

        print('>> * >> * >> TAKNG MEASUREMENTS')
        df, bin_defs, start_date, end_date, ts_info = self.df, self.bin_defs, self.ref_start, self.ref_end, self.ts_info
        step_size = self.step_size

        print('>>> MEASURING PROPORTIONS')
        self._default_proportions = get_default_proportions(df, pd.to_datetime(end_date) - pd.DateOffset(months=3), end_date)

        print('>>> CALCULATING AGEING PROPORTIONS')
        age_out_ratios = ageing_probs_per_bracket(bin_defs, step_size)
        print(age_out_ratios)

        print('>>> MEASURING DAILY TRANSITION PROBS')
        pops = get_daily_pops_new_way(df, start_date, end_date)
        #t_probs = transition_probs_per_bracket(df, bin_defs, start_date, end_date)
        t_probs = get_daily_transitions_new_way(df, pops)
        self.t_probs = t_probs
        print('T matrices (coming soon)')

        for bracket, t_mat in t_probs.items():
            print(str(bracket) + ':', t_mat, sep='\n')

        print('>>> CALCULATING STEP TRANSITON MATRICES')
        precalced_transition_matrices = calculate_timestep_transition_matrices(ts_info, t_probs)
        max_step_t_mats = precalced_transition_matrices[max(precalced_transition_matrices)]

        #print((f'{ab}:\n {T.to_json()}\n' for ab, T in max_step_t_mats.items()), sep='\n')

        print('>>> CALCULATING ENTRY RATES')

        entrance = daily_entrants_per_bracket(df, bin_defs, start_date, end_date)
        # - - - - - - - -- -  -- - - - -  - -  -  - - -
        print(f'[*]] * ****%%%(( ENTRANTS )) \n')
        for bracket, entrants_df in entrance.items():
            print(str(bracket) + ':', entrants_df, sep='\n')
        # - - - - - - - -- -  -- - - - -  - -  -  - - -

        self.daily_probs = t_probs
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
        age_out_ratios = self.age_out_ratios
        next_pop = self.initial_pop.copy()
        adj_next_pop = self.initial_pop.copy()
        date_vars = pd.Series(data=1, index=next_pop.index)
        adj_date_vars = adj_next_pop.copy()
        var_df = future_pop.copy()
        adj_var_df = future_pop.copy()
        age_mats = self.t_probs.copy()

        A_DF = pd.DataFrame(data=pd.NA, columns=future_pop.columns, index=future_pop.index)
        T_DF = A_DF.copy()
        E_DF = A_DF.copy()

        ## TRACKERS
        # initialise tracker of time since the start of the prediction. Variances are supposed to increase with time.
        days_so_far = 0
        # initialise tracker of the cummulative multiplication of transition matrices over time.
        T_so_far = {}
        for age_bin, t_mat in age_mats.items():
            T_so_far[age_bin] = pd.DataFrame(data=1, index=t_mat.index, columns=t_mat.columns)

        for date in future_pop.index:
            step_days = ts_info.loc[date, 'step_days']
            days_so_far += step_days
            print(f"* * * * * * * * {date} ")
            prev_pop = next_pop.copy()
            print('PREV POPS:\n', prev_pop)
            print('Making children older...')
            aged_pop = apply_ageing(prev_pop, age_out_ratios)

            ageing_changes = aged_pop - prev_pop

            if adjustments:
                adj_prev_pop = adj_next_pop.copy()
                adj_aged_pop = apply_ageing(adj_prev_pop, age_out_ratios)
            print('Moving children around...')

            next_pop.loc[:, :] = 0
            for age_bracket in next_pop.index.get_level_values('age_bin').unique():
                T = precalced_transition_matrices[step_days][age_bracket]

                next_pop[age_bracket] = T.dot(aged_pop[age_bracket])

                if adjustments:
                    adj_next_pop[age_bracket] = T.dot(adj_next_pop[age_bracket]) + entrant_rates[age_bracket] * step_days
                    adj_next_pop = apply_adjustments(adj_next_pop.copy(), adjustments, step_days)

            transition_changes = next_pop - aged_pop
            post_transition_pop = next_pop.copy()
            for age_bracket in next_pop.index.get_level_values('age_bin').unique():
                next_pop[age_bracket] += entrant_rates[age_bracket] * step_days

            entrant_changes = next_pop - post_transition_pop

            future_pop.loc[date] = next_pop
            if adjustments:
                adjusted_future_pop.loc[date] = adj_next_pop

            A_DF.loc[date] = ageing_changes
            E_DF.loc[date] = entrant_changes
            T_DF.loc[date] = transition_changes

        self.A_DF = A_DF
        self.E_DF = E_DF
        self.T_DF = T_DF


        self.future_pop = future_pop  # now we can convert these to csv/whatever and send to the frontend
        self.upper_pop, self.lower_pop = deviation_bounds(future_pop, var_df)
        if adjustments:
            self.adjusted_future_pop = adjusted_future_pop
            self.adj_upper_pop, self.adj_lower_pop = deviation_bounds(adjusted_future_pop, adj_var_df)

    def calculate_costs(self, cost_params):
        if cost_params['proportions'] is None:
            cost_params['proportions'] = self.default_proportions
        future_costs = calculate_costs(self.future_pop, **cost_params)
        adjustments = self.adjustments
        if adjustments:
            adjusted_future_costs = calculate_costs(self.adjusted_future_pop, **cost_params)

        past_cost_params = cost_params.copy()
        past_cost_params['inflation'] = None
        past_costs = calculate_costs(self.historic_pop, **cost_params)
        self.past_costs = past_costs
        self.future_costs = future_costs
        if adjustments:
            self.adjusted_future_costs = adjusted_future_costs

    def print_everything(self):

        # model_params
        print('>>> PARAMS',
        'start_date:', self.start_date,
        'ref_start:', self.ref_start,
        'ref_end:', self.ref_end,
        'end_date:', self.end_date,
        'horizon_date:', self.horizon_date,
        'step_size:', self.step_size, sep='\n')

        # stuff that will be calculated
        self.ts_info,


        print('>>> POPS',
        'historic_pop',
        self.historic_pop.to_string(),
        'future pop',
        self.future_pop.to_string(),
        'init pop',
        self.initial_pop.to_string(), sep='\n')

        print('>>> MODEL SPEC',
            'ageing',
            self.age_out_ratios,
            'one day probs',
            *[f'{ab}:\n {T.to_string()}\n\n' for ab, T in self.daily_probs.items()],
            'max step probs',
            f'(biggest step: {max(self.step_probs)})',
            *[f'{ab}:\n {T.to_string()}\n\n' for ab, T in self.step_probs[max(self.step_probs)].items()],

            'daily entrants',
            self.entrant_rates,

            '_default_propotions',
            self.default_proportions, sep='\n'
        )

        print('>>> MOVEMENTS')
        print('\n### ageing')
        print(self.A_DF.to_string())
        print('\n### entrants')
        print(self.E_DF.to_string())
        print('\n### transitions')
        print(self.T_DF.to_string())


    @property
    def default_proportions(self):
        # map it into flat structure expected by frontend.
        return self._default_proportions

    @property
    def csv_costs(self):
        base_csv = pd.concat([self.past_costs, self.future_costs]).to_csv()
        return base_csv

    @property
    def adj_csv_costs(self):
        adj_csv = pd.concat([self.past_costs, self.adjusted_future_costs]).to_csv()
        return adj_csv
        
    @property
    def csv_pops(self):
        base_csv = pd.concat([self.historic_pop, self.future_pop]).to_csv()
        return base_csv
    
    @property
    def adj_csv_pops(self):
        adj_csv = pd.concat([self.historic_pop, self.adjusted_future_pop]).to_csv()
        return adj_csv


    @property
    def base_pop_graph(self):
        df = pd.concat([self.historic_pop, self.future_pop])
        forecast_start_date = pd.to_datetime(self.end_date)
        return self.gen_pop_graph(df, forecast_start_date)

    @property
    def adj_pop_graph(self):
        df = pd.concat([self.historic_pop, self.adjusted_future_pop])
        forecast_start_date = pd.to_datetime(self.end_date)
        return self.gen_pop_graph(df, forecast_start_date)

    @property
    def base_cost_graph(self):
        df = pd.concat([self.past_costs, self.future_costs])
        forecast_start_date = pd.to_datetime(self.end_date)
        return self.gen_cost_graph(df, forecast_start_date)

    @property
    def adj_cost_graph(self):
        df = pd.concat([self.past_costs, self.adjusted_future_costs])
        forecast_start_date = pd.to_datetime(self.end_date)
        return self.gen_cost_graph(df, forecast_start_date)


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

        return tracey_beaker

    def gen_cost_graph(self, df, forecast_start_date):
        # fragile container of trace objects to be drawn by plotly.js
        tracey_beaker = [
            {
                'x': df.index.strftime('%Y-%m-%d').to_list(),
                'y': df[col].fillna(-1).to_list(),
                'type': 'scatter',
                'stackgroup': 'one',
                'name': ' - '.join(col)
             } for col in df
        ]

        # noinspection PyTypeChecker
        tracey_beaker.append(
            {'x': [forecast_start_date.strftime('%Y-%m-%d'), ] * 2,
             'y': [0, df.sum(axis=1).max()],
             'type': 'scatter',
             'line': {'dash': 'dot',
                      'width': 2},
             'mode': 'lines',
             'name': 'Forecast start'}
        )

        return tracey_beaker
