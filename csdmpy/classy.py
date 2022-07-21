from dataclasses import field

from marshmallow_dataclass import dataclass
from datetime import date
from typing import Mapping, Any

from csdmpy.config import age_brackets
from csdmpy.super_model import *
from csdmpy.costs import calculate_costs
from csdmpy.utils import deviation_bounds


@dataclass(frozen=True)
class ModelParams:
    history_start: date  # these should be dates but im doing late night hacky business
    reference_start: date
    reference_end: date
    history_end: date
    prediction_end: date
    step_size: int = 4
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

    def __init__(self, df=None, model_params: ModelParams = None, adjustments=None):
        print('INITTING MODEL INISTANCE')
        print('PAMS:', model_params)
        print('ADJS:', adjustments)
        self.df = df

        self.start_date = model_params.history_start
        self.ref_start = model_params.reference_start
        self.ref_end = model_params.reference_end
        self.end_date = model_params.history_end
        self.horizon_date = model_params.prediction_end
        self.step_size = f'{model_params.step_size}m'
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

        pops = get_daily_pops_new_way(df, start_date, end_date)
        #t_probs = transition_probs_per_bracket(df, bin_defs, start_date, end_date)
        t_probs = get_daily_transitions_new_way(df, pops)
        self.t_probs = t_probs
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
        date_vars = pd.Series(data=1, index=next_pop.index)
        adj_date_vars = adj_next_pop.copy()
        var_df = future_pop.copy()
        adj_var_df = future_pop.copy()
        age_mats = self.t_probs.copy()

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
            print('Making children older...')
            next_pop = apply_ageing(next_pop, {'fake': 'fake',
                                               'records': 'records'})
            print('Moving children around...')
            for age_bracket in next_pop.index.get_level_values('age_bin').unique():
                T = precalced_transition_matrices[step_days][age_bracket]
                # store present pop value so that it can be used in variance calculation.
                this_pop = next_pop.copy()

                next_pop[age_bracket] = T.dot(next_pop[age_bracket]) + entrant_rates[age_bracket] * step_days
                if adjustments:
                    adj_this_pop = adj_next_pop.copy()
                    adj_next_pop[age_bracket] = T.dot(adj_next_pop[age_bracket]) + entrant_rates[age_bracket] * step_days
                    adj_next_pop = apply_adjustments(adj_next_pop.copy(), adjustments, step_days)
                
                ## VARIANCE
                # M^t where M is daily transition probabilities and t is time so far.
                T_full = T_so_far[age_bracket].multiply(T) # should this be matrix or elementwise multiplication?
                T_so_far[age_bracket] = T_full
                # M^t x (1 – M^t) where x represents elementwise multiplication.
                one_minusT = 1 - T_full
                tran_mat = T_full.multiply(one_minusT)
                if date == self.ref_start:
                    # at the start of the prediction, the reference point, t is zero.
                    T = self.t_probs[age_bracket]
                    tran_mat = T.pow(0).multiply(1-T.pow(0))
                    days_so_far = 0
                # var[t0+t] = S(t) *  (M^t x (1 – M^t))  + R * t 
                # variances_t_later = (tran1day^cum_days x (1 - ran1day^cumdays)) * next_pop + entrants*(cum_days)
                date_vars[age_bracket] = tran_mat.dot(this_pop[age_bracket]) + (entrant_rates[age_bracket] * days_so_far)
                ## date_vars[age_bracket] = ((self.t_probs[age_bracket].pow(days_so_far)).multiply(1-(self.t_probs[age_bracket].pow(days_so_far)))).dot(this_pop[age_bracket]) + (this_pop[age_bracket] * days_so_far)
                if adjustments:
                    adj_date_vars[age_bracket] = tran_mat.dot(adj_this_pop[age_bracket]) + (adj_this_pop[age_bracket] * days_so_far)
                
            future_pop.loc[date] = next_pop
            var_df.loc[date] = date_vars
            if adjustments:
                adjusted_future_pop.loc[date] = adj_next_pop
                adj_var_df.loc[date] = adj_date_vars

        self.variances = var_df # to be removed

        self.future_pop = future_pop  # now we can convert these to csv/whatever and send to the frontend
        self.upper_pop, self.lower_pop = deviation_bounds(future_pop, var_df)
        if adjustments:
            self.adjusted_future_pop = adjusted_future_pop
            self.adj_upper_pop, self.adj_lower_pop = deviation_bounds(adjusted_future_pop, adj_var_df)

    def calculate_costs(self, cost_params):
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
