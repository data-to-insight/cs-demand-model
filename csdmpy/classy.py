import pandas as np
import numpy as np
from csdmpy.super_model import *
from csdmpy.utils import deviation_bounds

# from ingress import ...
from csdmpy.costs import calculate_costs


class Model:
    def __init__(
        self,
        df,
        start_date,
        end_date,
        horizon_date,
        step_size,
        bin_defs,
        cost_params=None,
    ):
        self.df = df

        self.start_date = start_date
        self.end_date = end_date
        self.horizon_date = horizon_date
        self.step_size = step_size
        self.bin_defs = bin_defs

        self.ts_info = None
        self.historic_pop = None
        self.future_pop = None
        self.lower_pop = None
        self.upper_pop = None
        self.initial_pop = None

        self.daily_probs = None
        self.step_probs = None
        self.entrant_rates = None

        if cost_params:
            self.cost_params = cost_params
            self.need_to_redo_costs = True
        else:
            self.cost_params = None

        self.need_to_rerun = True  # if params are updated

    # todo:
    def do_everything(self):
        self.set_up_time_series()
        self.measure_system()
        self.predict()
        self.calculate_costs()
        self.need_to_rerun = False

    def set_up_time_series(self):
        df, bin_defs, start_date, end_date, horizon_date, step_size = (
            self.df,
            self.bin_defs,
            self.start_date,
            self.end_date,
            self.horizon_date,
            self.step_size,
        )

        historic_pop = make_populations_ts(
            df, bin_defs, start_date, end_date, step_size
        ).sort_index()

        ts_info = make_date_index(
            end_date, horizon_date, step_size, align_end=False
        ).iloc[1:]
        future_pop = pd.DataFrame(columns=historic_pop.columns, index=ts_info.index)

        print("* *][*][*] * * (( HISTORIC POPS ))\n")
        print(historic_pop.to_string())
        print("[[*]] *]] * * * * (( FUTURE POPS ))\n")
        print(future_pop.to_string())
        initial_pop = historic_pop.loc[historic_pop.index.max()].copy()

        self.ts_info = ts_info
        self.historic_pop = historic_pop
        self.initial_pop = initial_pop
        self.future_pop = future_pop

    def measure_system(self):
        df, bin_defs, start_date, end_date, ts_info = (
            self.df,
            self.bin_defs,
            self.start_date,
            self.end_date,
            self.ts_info,
        )

        t_probs = transition_probs_per_bracket(df, bin_defs, start_date, end_date)

        print("[[[*] * * * * (( TRANS PROBS ))\n")

        for bracket, t_mat in t_probs.items():
            print(str(bracket) + ":", t_mat, sep="\n")

        precalced_transition_matrices = calculate_timestep_transition_matrices(
            ts_info, t_probs
        )

        entrance = daily_entrants_per_bracket(df, bin_defs, start_date, end_date)

        print(f"[*]] * ****%%%(( ENTRANTS )) \n")
        for bracket, entrants_df in entrance.items():
            print(str(bracket) + ":", entrants_df, sep="\n")
        print(precalced_transition_matrices[max(precalced_transition_matrices)])

        self.entrant_rates = entrance
        self.step_probs = precalced_transition_matrices

    def predict(self):
        df, bin_defs, start_date, end_date, ts_info, future_pop = (
            self.df,
            self.bin_defs,
            self.start_date,
            self.end_date,
            self.ts_info,
            self.future_pop,
        )
        precalced_transition_matrices = self.step_probs
        entrant_rates = self.entrant_rates
        next_pop = self.initial_pop

        # resulting data structure should be a DataFrame whose indices are identical to the forecast.
        pop_variance = pd.DataFrame(index=future_pop.index, columns=future_pop.columns)
        # replicate the row structure which contains the variances per child group, per date point.
        var_structure = next_pop.copy()

        for date in future_pop.index:
            step_days = ts_info.loc[date, "step_days"]
            print(f"* * * * * * * * {date} ")
            print("Making children older...")
            next_pop = apply_ageing(next_pop, {"fake": "fake", "records": "records"})
            print("Moving children around...")
            for age_bracket in next_pop.index.get_level_values("age_bin").unique():
                T = precalced_transition_matrices[step_days][age_bracket]

                # (1 – T)
                one_minusT = 1 - T.copy()
                # T x (1 – T)
                T_mult = T.copy().multiply(one_minusT)

                next_pop[age_bracket] = (
                    T.dot(next_pop[age_bracket])
                    + entrant_rates[age_bracket] * step_days
                )

                # The formula for calculating variance at any given time is Var[S(t)] =  (T x (1 – T)) * reference_pop + (entrant_rates * t )
                # When both sides are not scalar, x denotes elementwise multiplication, * denotes matrix multiplication. The (1 – M^t) operation is also elementwise.
                # elementwise: .multiply() , matrix multiplication : .dot()
                var_structure[age_bracket] = (
                    T_mult.dot(var_structure[age_bracket])
                    + entrant_rates[age_bracket] * step_days
                ) 

            future_pop.loc[date] = next_pop
            pop_variance.loc[date] = var_structure

        self.upper_pop, self.lower_pop = deviation_bounds(future_pop, pop_variance)

        self.future_pop = future_pop  # now we can convert these to csv/whatever and send to the frontend

    def calculate_costs(self, cost_params=None):
        if cost_params:
            self.cost_params.update(cost_params)
        elif self.cost_params:
            cost_params = self.cost_params
        else:
            raise ValueError("No cost_params!!!")
        future_costs = calculate_costs(self.future_pop, **cost_params)
        past_cost_params = cost_params.copy()
        past_cost_params["inflation"] = None
        past_costs = calculate_costs(self.historic_pop, **cost_params)

    def update_params(self, params):
        self.__init__(**params)
        self.need_to_rerun = True
