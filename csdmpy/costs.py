'''
Cost modelling

turning forecast values from model and cost estimates typed into frontend into cost projections
'''
import pandas as pd

# The structure of future_pop
"""
age_bin           10 to 16              16 to 18                         5 to 10           1 to 5 -1 to 1
placement_type      Foster       Resi     Foster      Resi  Supported     Foster      Resi Foster  Foster
2020-01-01      106.198122  21.232015   9.325041   1.16563   8.248693  19.960677  2.526994    0.0     0.0
2020-07-01      127.630768  25.508958  10.552913  1.319114  10.647734   23.95778  3.066877    0.0     0.0
2021-01-01      148.715533  29.714604  11.657999   1.45725  13.123215  27.882665  3.605005    0.0     0.0
2021-07-01      170.151327  33.988399  12.688585  1.586073  15.744095  31.865571  4.159085    0.0     0.0
2022-01-01       191.23918  38.190958  13.615888  1.701986  18.419487  35.776514  4.711155    0.0     0.0
"""
# The structure of the weekly costs expected from the user.
"""base_costs = {
        'Foster': 575 / 7,
        'Resi': 3915 / 7,
        'Supported': 1114 / 7,
        'All Other': 0,
    }
adjusted_costs = {
        'Foster': 600 / 7,
        'Resi': 3000 / 7,
        'Supported': 2000 / 7,
        'All Other': 0,
    }
cost_dict = {'base': base_costs, 'adjusted': adjusted_costs}"""

## FRONTEND CHECK: For every proportion type filled, a corresponding price must be filled in too.
## FRONTEND CHECK / INGRESS ADDITION: all percentages/numbers should be converted to a fraction of the total.

def proportion_split(df, proportions):
    """
    The example structures of the arguments are:
    df =  pd.DataFrame({'fives': [5, 10, 15, 20, 25, 30, 35, 40], 'tens': [10, 20, 30, 40, 50, 60, 70, 80]})
    proportions = {'fives':{'int':0.75, 'ext':0.20, 'an':0.05}}

    tens is intentionally left out of proportions to demonstrate what happens when a column name is missing.
    """
    df_made = pd.DataFrame()
    # create array structure that will be used to form a MultiIndex for the DataFrame
    index_list = [[],[]]

    for col in df.columns:
        # for each column
        
        if col not in proportions:
            # if no split is filled in by the user, add column name to proportions data but do not split.
            proportions[col] = {col: 1.0}
        # Get proportions dictionary. Use .get() so that missing columns return None instead of raising an error.
        proportion_dict = proportions.get(col)
        if proportion_dict != None:
            for name, value in proportion_dict.items():
                index_list[0].append(col)
                index_list[1].append(name)
                # create a new column to contain the proportion's values and maintain the name of the proportion.
                df_made[name] = df[col]*value
    # create MultiIndex that will be used to replace column names.
    index = pd.MultiIndex.from_arrays(index_list, names=['placements', 'sub-placements'])
    df_made.columns = index

    return df_made