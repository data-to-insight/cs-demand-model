'''
All the stuff for turning the csv bytes received from the frontend into
the pandas dataframes that the model itself takes as input
'''
import pandas as pd
import numpy as np
import os

def read_combined_903():
    path = r'C:\Users\michael.ogunkolade\pychr\csc-data-synthesizer\examples\fake903_5yrs'

    def combine_files_for_year(year):
        # Read the basic information
        header = pd.read_csv(os.path.join(path, str(year), 'header.csv'))
        episodes = pd.read_csv(os.path.join(path, str(year), 'episodes.csv'))

        # Convert dates to the right format
        header['DOB'] = pd.to_datetime(header['DOB'], format='%d/%m/%Y')
        episodes['DECOM'] = pd.to_datetime(episodes['DECOM'], format='%d/%m/%Y')
        episodes['DEC'] = pd.to_datetime(episodes['DEC'], format='%d/%m/%Y')

        print(episodes.columns, header.columns)

        return header.merge(episodes, how='inner', on='CHILD', suffixes=('_header', '_episodes'))

    combined = pd.concat([combine_files_for_year(y) for y in [2017, 2018, 2019, 2020, 2021]], ignore_index=True)
    print(f'Found {len(combined)} initial records for child.')

    # Just do some basic data validation checks
    assert not combined['CHILD'].isna().any()
    assert not combined['DECOM'].isna().any()

    ## Then clean up the episodes
    # We first sort by child, decom and dec, and make sure NAs are first (for dropping duplicates)
    combined.sort_values(['CHILD', 'DECOM', 'DEC'], inplace=True, na_position='first')

    # If a child has two episodes starting on the same day (usually if NA in one year and then done in next) keep the latest non-NA finish date
    combined.drop_duplicates(['CHILD', 'DECOM'], keep='last', inplace=True)
    print(f'{len(combined)} records remaining after removing episodes that start on the same date.')


    # If a child has two episodes with the same end date, keep the longer one. This also works for open episodes - if there are two open, keep the larger one.
    combined.drop_duplicates(['CHILD', 'DEC'], keep='first', inplace=True)
    print(f'{len(combined)} records remaining after removing episodes that end on the same date.')

    # If a child has overlapping episodes, shorten the earlier one
    decom_next = combined.groupby('CHILD')['DECOM'].shift(-1)
    change_ix = combined['DEC'].isna() | combined['DEC'].gt(decom_next)
    combined.loc[change_ix, 'DEC'] = decom_next[change_ix]

    print(f'Updated {change_ix.sum()} overlapping episodes.')

    # We can then randomize the ages. This probably should be replicable (hence the random seed.)
    rng = np.random.default_rng(42)
    combined['DOB'] = combined.groupby('CHILD')['DOB'].transform(lambda x: x + pd.Timedelta(days=rng.integers(0, 364)))

    return combined

def categorize_placement(code):
    if code in ['U1', 'U2', 'U3', 'U4', 'U5', 'U6']:
        return 'Foster'
    elif code in ['K2', 'R1']:
        return 'Resi'
    elif code in ['H5', 'P2']:
        return 'Supported'
    else:
        return 'Outside'


def get_daily_data(df):
    df = df.copy()
    # Create a dataframe with an entry for every child on every day between DECOM (inclusive) and DEC (exclusive)
    df['DEC_filled'] = (df['DEC'] - pd.Timedelta(days=1)).fillna(df['DEC'].max())

    df['placement_type_before'] = df.groupby('CHILD')['placement_type'].shift(1).fillna('Outside')
    df['placement_type_after'] = df.groupby('CHILD')['placement_type'].shift(-1).fillna('Outside')

    # If the placement before/after is not contiguous, we want to replace it with outside.
    df['DEC_before'] = df.groupby('CHILD')['DEC'].shift(1)
    df.loc[df['DEC_before'].isna() | df['DEC_before'].ne(df['DECOM']), 'placement_type_before'] = 'Outside'
    del df['DEC_before']

    df['DECOM_after'] = df.groupby('CHILD')['DECOM'].shift(-1)
    df.loc[df['DECOM_after'].notna() & df['DECOM_after'].ne(df['DEC']), 'placement_type_after'] = 'Outside'
    del df['DECOM_after']

    df["date"] = df.apply(
        lambda x: pd.date_range(x['DECOM'], x['DEC_filled']), axis=1
    )

    date_df = df.explode("date", ignore_index=True)

    date_df = date_df[date_df['date'] > '2016-04-01']

    # Add any other helper columns
    date_df['new_in'] = (date_df['date'] == date_df['DECOM']) & (
                date_df['placement_type_before'] != date_df['placement_type'])
    date_df['last_day'] = (date_df['date'].eq(date_df['DEC_filled']) & date_df['date'].ne(df['DEC'].max())) & (
                date_df['placement_type_after'] != date_df['placement_type'])
    date_df['age'] = (date_df['date'] - date_df['DOB']).dt.days / 365
    date_df['age_bucket'] = pd.cut(date_df['age'], bins=[-1.0, 4.5, 9.5, 15.5, 19.5])
    date_df['days_in_placement'] = (date_df['date'] - date_df['DECOM']).dt.days
    date_df['duration_bucket'] = pd.cut(date_df['days_in_placement'], bins=[-1, 180, 720, 10000])

    # Add helper columns around transition
    date_df['placement_tomorrow'] = date_df['placement_type']
    date_df.loc[date_df['last_day'], 'placement_tomorrow'] = date_df['placement_type_after'][date_df['last_day']]
    date_df['transition_tomorrow'] = date_df['placement_type'] + ' -> ' + date_df['placement_tomorrow']
    date_df['transition_tomorrow'] = date_df['transition_tomorrow'].astype(
        'category')  # Make this a category to make grouping easier
    date_df['placement_type_before'] = date_df['placement_type_before'].astype('category')
    date_df['placement_type'] = date_df['placement_type'].astype('category')
    date_df['placement_tomorrow'] = date_df['placement_tomorrow'].astype('category')

    # Confirm there is no issues with uniqueness
    results = date_df.groupby('date')['CHILD'].agg(['nunique', 'count'])
    assert (results['nunique'] == results['count']).all()

    return date_df

