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

    def __init__(self, df=None, model_params: ModelParams = None, adjustments=None):
        self.set_up_time_series()

        self.measure_system()

        self.predict()

    def set_up_time_series(self):

        historic_pop = make_populations_ts(df, bin_defs, start_date, end_date, step_size).sort_index()

        ts_info = make_date_index(end_date, horizon_date, step_size, align_end=False).iloc[1:]

        future_pop = pd.DataFrame(columns=historic_pop.columns, index=ts_info.index)


        initial_pop = historic_pop.loc[historic_pop.index.max()].copy().astype(float)

        if self.adjustments:
            self.adjusted_future_pop = future_pop.copy() # Here we make a copy of the future_pop dataframe if we have adjustments?
        else:
            self.adjusted_future_pop = None

    def measure_system(self):
        self._default_proportions = get_default_proportions(df, pd.to_datetime(end_date) - pd.DateOffset(months=3), end_date)

        age_out_ratios = ageing_probs_per_bracket(bin_defs, step_size)

        pops = get_daily_pops_new_way(df, start_date, end_date)

        t_probs = get_daily_transitions_new_way(df, pops)

        precalced_transition_matrices = calculate_timestep_transition_matrices(ts_info, t_probs)
        max_step_t_mats = precalced_transition_matrices[max(precalced_transition_matrices)]

        entrance = daily_entrants_per_bracket(df, bin_defs, start_date, end_date)



    def predict(self):
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
        if adjustments:
            self.adjusted_future_costs = adjusted_future_costs


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
