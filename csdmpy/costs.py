'''
Cost modelling

turning forecast values from model and cost estimates typed into frontend into cost projections
'''
import pandas as pd
import numpy as np
from csdmpy.super_model import step_to_days

## Functionality present
""" 
- generate time series of cost over forecasted population time period.
- process multiple scenarios. base, adjusted1, adjusted2 ... adjusted_n.
- Split population forecasts into sub placement locations per placement type.
- Process placement location proportions from user.
- Process a variable number of placement locations and names.

"""

# The structure of grouped_df which is passed in here as df
"""
placement_type      Foster       Resi  Supported
2020-01-01      135.483841  24.924639   8.248693
2020-07-01      162.141461  29.894949  10.647734
2021-01-01      188.256198  34.776859  13.123215
2021-07-01      214.705483  39.733557  15.744095
2022-01-01      240.631582  44.604098  18.419487
"""

## FRONTEND CHECK: For every proportion type filled, a corresponding price must be filled in too.
## FRONTEND CHECK / INGRESS ADDITION: all percentages/numbers should be converted to a fraction of the total.
## FRONTEND : All costs received from the user should be weekly costs.

def proportion_split(df, proportions):
    """
    This function splits the populations in the various placement types into placement locations.
    It shows how many children will be in each placement location.

    The example structures of the arguments are:
    df =  pd.DataFrame({'Foster': [5, 10, 15, 20, 25, 30, 35, 40], 'Supported': [10, 20, 30, 40, 50, 60, 70, 80]})
    proportions = {'Foster':{'friend_relative':0.75, 'in_house':0.20, 'IFA':0.05}}

    Supported is intentionally left out of proportions to demonstrate what happens when a column name is missing.
    """
    # copy over the date values contained in the index.
    df_made = pd.DataFrame(index =  df.index)
    # create array structure that will be used to form a MultiIndex for the DataFrame columns.
    index_list = [[],[]]

    for col in df.columns:
        # for each column        
        if col not in proportions:
            # if no split is filled in by the user, add column name to proportions data but do not split.
            # This is because, in the excel sheet, Supported placements are not split.
            proportions[col] = {col: 1.0}
        # Get proportions dictionary. Use .get() so that missing columns return None instead of raising an error.
        proportion_dict = proportions.get(col)
        if proportion_dict != None:
            for name, value in proportion_dict.items():
                index_list[0].append(col)
                index_list[1].append(name)
                # create a new column to contain the proportion's values and maintain the name of the proportion.
                '''TODO Make sure placement locations with the same name do not override themselves here. 
                    e.g in_house which is present in both Foster and Residential '''
                df_made[name] = df[col]*value
    # create MultiIndex that will be used to replace column names.
    print(df_made.columns)
    print(index_list)
    df_made.columns = pd.MultiIndex.from_arrays(index_list, names = ['placement_types', 'placement_locations'])
    return df_made

def get_step_costs(weekly_costs, step_size):
    """This function cummulates the weekly costs given by the user"""

    days = step_to_days(step_size)
    daily_costs = np.array(weekly_costs) / 7
    step_costs = daily_costs * days
    return step_costs

def create_cost_ts(df_made, location_costs, step_size, inflation = False):
    '''
    This function calculates the cost over time for each placement location in each placement type.

    location_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, }, 'Supported' : {'Sup': 40,}}
    '''
    ind_lst = [[],[]]
    vals_lst = []
    for placement_type in location_costs:
        
        for location, value in location_costs[placement_type].items():
            ind_lst[0].append(placement_type)
            ind_lst[1].append(location)
            vals_lst.append(value)
    vals_lst = get_step_costs(vals_lst, step_size)

    cols = pd.MultiIndex.from_arrays(ind_lst, names = ['placement_types', 'placement_locations'])
    # The cost array is replicated into a DataFrame whose index and columns are the same as df_made.
    cost_structure = pd.DataFrame(index =  df_made.index, columns = cols)
    if inflation == False:
        cost_structure.loc[ : , : ] = vals_lst
    elif inflation == True:
        pass
    costed_df = df_made.multiply(cost_structure)

    return costed_df

def calculate_costs(df_future, cost_dict, proportions, step_size, inflation = False):
    """
    The expected shape of cost_dict is 
    cost_dict = {'base': base_costs, 'adjusted': adjusted_costs}
    where base_costs and adjusted_costs are similar dictionaries of the form
    location_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, }, 'Supported' : {'Sup': 40,}}
    That is, base_location_costs = cost_dict['base_costs']

    The expected shape of proportions is the same as location_costs, however the numbers represent fractions/percentages
    of the population in each location type.
    """

    future_costs = {}
    proportioned_df = proportion_split(df_future, proportions)
    
    for scenario in cost_dict:
        # Scenarios are base, adjusted
        location_costs = cost_dict[scenario]     
        # Get the costs over the specified time period.
        cost_ts = create_cost_ts(df_made = proportioned_df, location_costs = location_costs, 
                                    step_size = step_size, inflation = inflation)
        future_costs[scenario] = cost_ts
    
    return future_costs