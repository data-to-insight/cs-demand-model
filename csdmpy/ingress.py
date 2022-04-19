'''
All the stuff for turning the csv bytes received from the frontend into
the pandas dataframes that the model itself takes as input
'''
import pandas as pd
import numpy as np
import os
from io import BytesIO
from .config import MAX_YEARS_OF_DATA, NOT_IN_CARE, table_headers


class UploadError(Exception):
    pass

def the_ingress_procedure(files_list):
    print(type(files_list))
    try:
        remaining_files = files_list.copy()
    except AttributeError:
        files_list = files_list.to_py()
        remaining_files = files_list.copy()

    yearly_dfs = {}
    empty_years = []
    for i in range(MAX_YEARS_OF_DATA):
        label = f"{i}_ago"

        matching_files, remaining_files = get_matching_uploads(remaining_files, label, return_remainder=True)

        if not matching_files:
            empty_years.append(label)

        year_dfs = identify_tables(matching_files, table_headers)

        merged_df = combine_files_for_year(year_dfs, i)

        yearly_dfs[label] = merged_df

    if not yearly_dfs:
        raise UploadError("No valid files received.")

    if remaining_files:
        # maybe just spit a warning + tell auntie goog.
        remaining_descriptions = {file['description'] for file in remaining_files}
        raise UploadError(f"Invalid file description(s) received: {', '.join(remaining_descriptions)}")

    all_903 = pd.concat(yearly_dfs)
    all_903 = read_combined_903(all_903)
    all_903['placement_type'] = all_903['PLACE'].apply(categorize_placement)
    all_903.sort_values(['CHILD', 'DECOM', 'DEC'], inplace=True, na_position='first')

    all_903['placement_type_after'] = (all_903
                                       .groupby('CHILD')
                                           ['placement_type']
                                       .shift(-1)
                                       .fillna(NOT_IN_CARE))
    out_after_mask = (
        (all_903['CHILD'] == all_903['CHILD'].shift(-1))
        & (all_903['DEC'] != all_903['DECOM'].shift(-1))
    )
    all_903.loc[out_after_mask, 'placement_type_after'] = NOT_IN_CARE

    all_903['placement_type_before'] = (all_903
                                        .groupby('CHILD')
                                            ['placement_type']
                                        .shift(1)
                                        .fillna(NOT_IN_CARE))
    out_before_mask = (
        (all_903['CHILD'] == all_903['CHILD'].shift(1))
        & (all_903['DECOM'] != all_903['DEC'].shift(1))
    )
    all_903.loc[out_before_mask, 'placement_type_before'] = NOT_IN_CARE

    # date_df = get_daily_data(all_903)

    return all_903


def get_matching_uploads(files_list, label, return_remainder=False):
    matching_files = []
    remaining_files = []
    for file in files_list:
        if file['description'] == label:
            matching_files.append(file)
        else:
            remaining_files.append(file)
    if return_remainder:
        return matching_files, remaining_files
    else:
        return matching_files


def identify_tables(matching_files, table_headers):
    year_dfs = {}
    for file in matching_files:
        try:
            df = pd.read_csv(BytesIO(file['fileText']))
        except UnicodeError:
            raise UploadError(f"Failed to decode one or more files. Try opening the text "
                              f"file(s) in Notepad, then 'Saving As...' with the UTF-8 encoding")
        # TODO: figure out what we're expecting to be excepting here
        except:
            label = file['description']
            raise UploadError(f"Failed to read file uploaded under {label} - ensure all files are valid CSVs!")

        for table_name, headers in table_headers.items():  # dict - {table_name: set_of_columns for i in whatever}
            print(table_name, headers)
            if len(set(headers) - set(df.columns)) == 0:
                print(table_name, 'FOUND')
                if table_name in year_dfs:
                    raise UploadError(f"Already added {table_name} - make sure you only add each table once!")
                else:
                    year_dfs[table_name] = df
                    #table_id = '_'.join((label, table_name))
    return year_dfs


def combine_files_for_year(the_years_files, years_ago):
    print(the_years_files)
    try:
        header = the_years_files['Header']
        episodes = the_years_files['Episodes']
    except KeyError as e:
        raise UploadError(f"Did not receive [{e.args[0]}] for [{years_ago} years ago]")
    # Read the basic information
    # Convert dates to the right format
    header['DOB'] = pd.to_datetime(header['DOB'], format='%d/%m/%Y')
    episodes['DECOM'] = pd.to_datetime(episodes['DECOM'], format='%d/%m/%Y')
    episodes['DEC'] = pd.to_datetime(episodes['DEC'], format='%d/%m/%Y')

    print(episodes.columns, header.columns, sep='\n\n')

    return header.merge(episodes, how='inner', on='CHILD', suffixes=('_header', '_episodes'))


def read_combined_903(combined):
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

    return combined

def categorize_placement(code):
    if code in ['U1', 'U2', 'U3', 'U4', 'U5', 'U6']:
        return 'Foster'
    elif code in ['K2', 'R1']:
        return 'Resi'
    elif code in ['H5', 'P2']:
        return 'Supported'
    else:
        return 'Other'



def get_daily_data(df, ):
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
    date_df['age'] = (date_df['date'] - date_df['DOB']).dt.days / 365.25
    date_df['age_bucket'] = pd.cut(date_df['age'], bins=[-1.0, 4.5, 9.5, 15.5, 19.5])

    #
    date_df['age_slice'] = pd.cut(date_df['age'], bins=np.linspace(-0.75, 21.0, int(21.75*4) + 1))

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

