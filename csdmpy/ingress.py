'''
All the stuff for turning the csv bytes received from the frontend into
the pandas dataframes that the model itself takes as input
'''
import pandas as pd
import numpy as np
import os
from io import BytesIO
from .config import MAX_YEARS_OF_DATA, NOT_IN_CARE, table_headers, age_brackets, UploadError
from warnings import warn
from .utils import split_age_bin

hacky_timez_key_map = {
    '2021/22': '0_ago',
    '2020/21': '1_ago',
    '2019/20': '2_ago',
    '2018/19': '3_ago',
    '2017/18': '4_ago',
}

def hacky_timez_input_workaround(files_dict):
    # this should not be a thing
    # update the_ingress_procedure to make use of the dict structure from the frontend
    files_list = []
    for year in files_dict:
        try:
            x_ago = hacky_timez_key_map[year]
        except KeyError:
            warn(f'idk what {year} is; discarding {len(files_dict[year])} files.')
            continue
        except TypeError:
            print(year)
            print(type(year), type(hacky_timez_key_map))
        for file in files_dict[year]:
            files_list.append({
                'description': x_ago,
                'fileText': file['fileText'],
            })
    return files_list


def the_ingress_procedure(files_list):
    # !!!
    try:
        files_list = files_list.to_py()
    except AttributeError:
        pass
    if isinstance(files_list, dict):
        files_list = hacky_timez_input_workaround(files_list)
    # !!!

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
        if year_dfs:
            merged_df = combine_files_for_year(year_dfs, i)
            yearly_dfs[label] = merged_df

    if not yearly_dfs:
        raise UploadError("No valid files received.")

    if remaining_files:
        # maybe just spit a warning + tell auntie goog.
        remaining_descriptions = {file['description'] for file in remaining_files}
        warn(f"Invalid file description(s) received: { ', '.join(remaining_descriptions) }")

    all_903 = pd.concat(yearly_dfs)
    all_903 = read_combined_903(all_903)
    all_903['placement_type'] = all_903['PLACE'].apply(categorize_placement)
    all_903['placement_subtype'] = all_903['PLACE'].apply(name_subplacement)
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
                                        .groupby('CHILD')['placement_type']
                                        .shift(1)
                                        .fillna(NOT_IN_CARE))
    out_before_mask = (
        (all_903['CHILD'] == all_903['CHILD'].shift(1))
        & (all_903['DECOM'] != all_903['DEC'].shift(1))
    )

    def get_in_the_bin(age):
        for bracket in sorted(age_brackets.keys()):
            lower, upper = split_age_bin(bracket)
            if lower <= age < upper:
                return bracket
        warn('Failed to place child in bin!')

    all_903.loc[out_before_mask, 'placement_type_before'] = NOT_IN_CARE

    all_903['age_bin'] = all_903['age'].apply(get_in_the_bin)
    all_903['end_age_bin'] = all_903['end_age'].apply(get_in_the_bin)

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
            if len(set(headers) - set(df.columns)) == 0:
                if table_name in year_dfs:
                    raise UploadError(f"Already added {table_name} - make sure you only add each table once!")
                else:
                    year_dfs[table_name] = df
                    #table_id = '_'.join((label, table_name))
    return year_dfs


def combine_files_for_year(the_years_files, years_ago):
    print(f'Files received for {years_ago} years ago: {list(the_years_files.keys())}')
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

    merged = header.merge(episodes, how='inner', on='CHILD', suffixes=('_header', '_episodes'))

    merged['age'] = (merged['DECOM'] - merged['DOB']).dt.days / 365.24
    merged['end_age'] = (merged['DEC'] - merged['DOB']).dt.days / 365.24

    return merged


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

# TODO fill in real codes. This mapping has not been confirmed. 
def name_subplacement(code):
    if code in ['U1', 'U2', 'U3']:
        return 'foster_friend_relative'
    elif code in ['U4', 'U5']:
        return 'foster_in_house'
    elif code in ['U6']:
        return 'foster_IFA'
    elif code in ['R1']:
        return 'resi_in_house'
    elif code in ['K2']:
        return 'resi_external'
    elif code in ['H5', 'P2']:
        return 'supported_supported'
    elif code in ['K1']:
        return 'other_secure_home'
    elif code in ['P1', 'R3']:
        return 'other_placed_with_family'
    else:
        return 'other_other'

