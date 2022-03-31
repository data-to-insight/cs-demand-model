'''
All the bits and pieces for turning the input table(s) into a transition rates time series then into a forecast

Probably with a class for keeping track of everything and making the necessary
bits accessible/modifiable, along the lines of 903validator.Validator

Could be split out into subcomponents as Tambe suggested: Transitions

Somewhere we'll have to have a structure to hold hypothetical 'adjustments' added in frontend.
'''
import pandas as pd
import numpy as np


def get_raw_placement_transition_data(date_df, bucket_type='age_bucket', freq='1D'):
    daily_data = \
    date_df.groupby([pd.Grouper(key='date', freq=freq), 'placement_type', bucket_type, 'placement_tomorrow'],
                    observed=False)[['CHILD']].count().reset_index()
    # Normalize by each day's children to get rate
    daily_data['total_in_placement'] = daily_data.groupby(['date', 'placement_type', bucket_type])['CHILD'].transform(
        sum)
    daily_data['day_probability'] = daily_data['CHILD'] / daily_data['total_in_placement']

    daily_data.set_index('date', inplace=True)
    return daily_data


from functools import partial


# These all return an average of col_name, within the groups defined by groupers, and based on date_end.

def all_time_mean_before_date(data, date_end, groupers, col_name):
    return data[data.index < date_end].groupby(groupers)[col_name].mean()


def period_mean_before_date(days_back, data, date_end, groupers, col_name):
    date_start = date_end - pd.Timedelta(days=days_back)
    return data[(data.index >= date_start) & (data.index < date_end)].groupby(groupers)[col_name].mean()


def exponential_mean(half_life, data, date_end, groupers, col_name):
    return data[data.index < date_end].groupby(groupers)[col_name].apply(
        lambda x: x.ewm(halflife=half_life).mean().iloc[-1])


def get_transition_matrix_for_date(date_df, date, agg=None, bucket_type='age_bucket'):
    if agg is None:
        agg = all_time_mean_before_date
    raw_data = get_raw_placement_transition_data(date_df, bucket_type=bucket_type, freq='1D')

    transition_matrix = agg(raw_data, date, ['placement_type', bucket_type, 'placement_tomorrow'],
                            'day_probability').unstack()
    return transition_matrix


def get_ingress_rates_for_date(date_df, date, agg=None):
    if agg is None:
        agg = all_time_mean_before_date
    ingress_daily = date_df.groupby(['date', 'placement_type_before', 'placement_type', 'age_bucket'])[
        ['new_in']].sum().reset_index(level=[1, 2, 3])
    ingress_daily = ingress_daily[ingress_daily['placement_type_before'].eq('Outside')]
    aggregate_rate = agg(ingress_daily, date, ['placement_type', 'age_bucket'], 'new_in').reset_index()

    return dict(zip(zip(aggregate_rate['placement_type'], aggregate_rate['age_bucket']), aggregate_rate['new_in']))


def get_initial_populations(date_df, date):
    populations = date_df.groupby(['date', 'placement_type', 'age_bucket'])['CHILD'].count().reset_index()

    populations = populations[populations['date'] == date]
    return dict(zip(zip(populations['placement_type'], populations['age_bucket']), populations['CHILD']))


def get_aging_out_probabilities(date_df, date, agg=None):
    """Infers the probability (daily) of aging out of each of the buckets"""
    if agg is None:
        agg = all_time_mean_before_date
    next_age_bucket = date_df.groupby('CHILD')['age_bucket'].shift(-1)
    date_df['aged_out'] = (date_df['age_bucket'] != next_age_bucket) & next_age_bucket.notna()

    daily_aged_out = date_df.groupby(['date', 'age_bucket']).agg({'aged_out': 'sum', 'CHILD': 'count'}).reset_index(
        level=1)
    daily_aged_out['rate'] = daily_aged_out['aged_out'] / daily_aged_out['CHILD']

    agg_df = agg(daily_aged_out, date, ['age_bucket'], 'rate')

    return dict(zip(agg_df.index, agg_df.values))


def _broadcasted_multinomial(x, probs):
    total_pop = x
    output = []

    for i, p in enumerate(probs[:-1]):
        total_prob = sum(probs[i:])

        if total_prob > 0:
            assigned = np.random.binomial(x, p / total_prob)
        else:
            assigned = np.zeros_like(total_pop)
        output.append(assigned)
        total_pop -= assigned

    output.append(total_pop)
    return np.vstack(output)


def run_sample(num_samples, start_date, number_days, buckets, ingress_rates, transition_matrix,
               age_out_daily_probs=None):
    # Get these in vector form to make work easier
    bucket_labels = [
        ('Foster', pd.Interval(-1.0, 4.5, closed='right')),
        ('Foster', pd.Interval(4.5, 9.5, closed='right')),
        ('Foster', pd.Interval(9.5, 15.5, closed='right')),
        ('Foster', pd.Interval(15.5, 19.5, closed='right')),
        ('Resi', pd.Interval(4.5, 9.5, closed='right')),
        ('Resi', pd.Interval(9.5, 15.5, closed='right')),
        ('Resi', pd.Interval(15.5, 19.5, closed='right')),
        ('Supported', pd.Interval(15.5, 19.5, closed='right')),
        ('All Other', None),
    ]

    next_age_buckets = {
        pd.Interval(-1.0, 4.5, closed='right'): pd.Interval(4.5, 9.5, closed='right'),
        pd.Interval(4.5, 9.5, closed='right'): pd.Interval(9.5, 15.5, closed='right'),
        pd.Interval(9.5, 15.5, closed='right'): pd.Interval(15.5, 19.5, closed='right'),
        pd.Interval(15.5, 19.5, closed='right'): None,
    }

    # Pre-calculate this for performance
    if age_out_daily_probs is None:
        print('Assuming uniform aging out distribution as not provided...')
        age_out_daily_probs = {
            age_bucket: 1 / ((min([19, age_bucket.right]) - max([0, age_bucket.left])) * 365)
            for age_bucket in next_age_buckets
        }

    populations = {
        label: np.array([buckets.get(label, 0) for _ in range(num_samples)])
        for label in bucket_labels
    }
    results = {start_date: populations}

    # Pre-calculate these samples to improve performance
    ingress_samples = {
        label: np.random.poisson(ingress_rates.get(label, 0), size=(num_samples, number_days)) for label in
        bucket_labels
    }

    date = start_date
    for i in range(number_days):
        date += pd.Timedelta(days=1)

        # First, do the new ingress
        new_population = {
            label: ingress_samples[label][:, i] for label in populations
        }

        # Then age the population
        # We assume uniform aging across the bucket
        # TODO: We can probably do better than this
        aged_populations = {label: np.zeros_like(populations[label]) for label in populations}
        for label, current_popn in populations.items():
            name, age_bucket = label
            if age_bucket is None:
                aged_populations[label] += current_popn
            else:
                age_out_daily_prob = age_out_daily_probs[age_bucket]
                age_up = np.random.binomial(current_popn, age_out_daily_prob)
                stay_same = current_popn - age_up

                aged_populations[label] += stay_same

                next_age = next_age_buckets[age_bucket]
                # We never age out the 16-18 bucket, as these should deplete naturally
                if next_age is not None:
                    aged_populations[(name, next_age)] += age_up

        # Then transition the population
        for label, population in aged_populations.items():
            name, age_bucket = label
            if name != 'All Other':
                # First, get the transition within the age bucket
                transitions = transition_matrix.loc[label]
                new_distribution = _broadcasted_multinomial(population,
                                                            transitions.values)  # returns num_transitions * num_samples

                # Then assign each population change appropriately
                for transition_label, new_popn in zip(transitions.index, new_distribution):
                    bucket_label = (transition_label, age_bucket)

                    if bucket_label in new_population:
                        # Straightforward - assign this straightaway
                        new_population[bucket_label] += new_popn
                    else:
                        if transition_label != 'Outside':
                            # This is a rare transition to a higher-age group (e.g. wanting to move a 15 year old to Supported) - just put in the higher bucket
                            target_label = min([l for l in bucket_labels if l[0] == transition_label])
                            new_population[target_label] += new_popn
                        else:
                            new_population[('All Other', None)] += new_popn
            else:
                # All Other population just gets directly tracked
                new_population[('All Other', None)] += population

        populations = new_population
        results[date] = populations

    all_results = []
    for i in range(num_samples):
        result = {date: {label: pop[i] for label, pop in res.items()} for date, res in results.items()}
        all_results.append(pd.DataFrame.from_dict(result, orient='index', columns=bucket_labels))

    return all_results


def get_initial_data(date_df, start_date, agg=None):
    # Get initial parameters at the start date
    buckets = get_initial_populations(date_df, start_date)
    ingress_rates = get_ingress_rates_for_date(date_df, start_date, agg=agg)
    transition_matrix = get_transition_matrix_for_date(date_df, start_date, agg=agg)
    age_out_daily_probs = get_aging_out_probabilities(date_df, start_date, agg=agg)
    return buckets, ingress_rates, transition_matrix, age_out_daily_probs


def create_samples(date_df, start_date, number_days, number_samples, agg=None):
    buckets, ingress_rates, transition_matrix, age_out_daily_probs = get_initial_data(date_df, start_date, agg=agg)

    samples = run_sample(
        num_samples=number_samples,
        start_date=start_date,
        number_days=number_days,
        buckets=buckets,
        ingress_rates=ingress_rates,
        transition_matrix=transition_matrix,
        age_out_daily_probs=age_out_daily_probs,
    )

    daily_costs = {
        'Foster': 575 / 7,
        'Resi': 3915 / 7,
        'Supported': 1114 / 7,
        'All Other': 0,
    }

    def get_cost(x):
        cost = 0
        for col in x.index:
            cost += daily_costs[col[0]] * x[col]
        return cost

    samples_df = pd.DataFrame(index=samples[0].index)
    high_level_groups = set(c[0] for c in samples[0].columns)
    for col in high_level_groups:
        # Produces a num_samples x num_days matrix
        level_cols = [c for c in samples[0].columns if c[0] == col]
        col_data = np.vstack([s[level_cols].sum(axis=1) for s in samples])
        samples_df[col + '_mean'] = np.mean(col_data, axis=0)
        samples_df[col + '_std'] = np.std(col_data, axis=0)
        samples_df[col + '_90th'] = np.percentile(col_data, 90, axis=0)
        samples_df[col + '_10th'] = np.percentile(col_data, 10, axis=0)

    cost_data = np.vstack([s.apply(get_cost, axis=1) for s in samples])
    # Keep track of the costs to date, and project to an annual basis
    annual_cost_data = np.cumsum(cost_data, axis=1)
    annual_cost_data /= np.arange(1, cost_data.shape[1] + 1) / 365

    for col, col_data in [('DailyCost', cost_data), ('AnnCost', annual_cost_data)]:
        samples_df[col + '_mean'] = np.mean(col_data, axis=0)
        samples_df[col + '_std'] = np.std(col_data, axis=0)
        samples_df[col + '_90th'] = np.percentile(col_data, 90, axis=0)
        samples_df[col + '_10th'] = np.percentile(col_data, 10, axis=0)

    means_df = pd.DataFrame(index=samples[0].index)
    for col in samples[0].columns:
        # Produces a num_samples x num_days matrix
        col_data = np.vstack([s[col] for s in samples])
        means_df[col] = np.mean(col_data, axis=0)

    return samples_df, means_df
