import pandas as pd

from csdmpy.constants import AgeBracket


def predict(self, initial_population: pd.DataFrame, t_matrices: dict[AgeBracket, pd.DataFrame]):
    # entrant_rates = self.entrant_rates
    # age_out_ratios = self.age_out_ratios
    # precalced_transition_matrices = self.step_probs

    days_so_far = 0
    # next_pop.loc[:, :] = 0

    for date in initial_population.index:
        step_days = 1
        days_so_far += step_days
        aged_pop = apply_ageing(prev_pop, age_out_ratios)

        for age_bracket in AgeBracket:
            T = precalced_transition_matrices[step_days][age_bracket]
            next_pop[age_bracket] = T.dot(aged_pop[age_bracket])

        for age_bracket in next_pop.index.get_level_values('age_bin').unique():
            next_pop[age_bracket] += entrant_rates[age_bracket] * step_days

        future_pop.loc[date] = next_pop

    self.future_pop = future_pop


def apply_ageing(pops, ageing_dict):
    aged_pops = pd.Series()
    for age_bin in AgeBracket:
        aged_out = pops.xs(age_bin, level='age_bin', drop_level=False) * ageing_dict[age_bin]
        aged_pops[age_bin] = pops.xs(age_bin, level='age_bin', drop_level=False) - aged_out
        next_bin = age_bin.next()
        if next_bin:
            aged_pops[next_bin] = pops.xs(next_bin, level='age_bin', drop_level=False) + aged_out


        try:
            next_ab = age_bin_list[age_bin_list.index(ab) + 1]
        except IndexError:
            print(f'no age bracket above {ab} - {aged_out.sum()} out in the world')
            continue
        mi = pd.MultiIndex.from_product([(next_ab, ), pops[ab].index], names=['age_bin', 'placement_type'])
        aged_pops[mi] = pops[mi].values + aged_out[ab].values # is this safe?
    return aged_pops