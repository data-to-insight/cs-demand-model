from csdmpy import ingress, model
import pandas as pd

test_903_dir = os.path.join(os.path.dirname(__file__), 'fake903_5yrs')
year_list = [2017, 2018, 2019, 2020, 2021]
tables_needed = ('header', 'episodes')
table_headers = {
    'Episodes':
        'CHILD,DECOM,RNE,LS,CIN,PLACE,PLACE_PROVIDER,DEC,REC,REASON_PLACE_CHANGE,HOME_POST,PL_POST'.split(','),
    'Header':
        'CHILD,SEX,DOB,ETHNIC,UPN,MOTHER,MC_DOB'.split(',')
}
files_list = []
for year in year_list:
    year_dir = os.path.join(test_903_dir, str(year))
    label = str(max(year_list) - year) + "_ago"
    for table_name in tables_needed:
        table_path = os.path.join(year_dir, table_name + '.csv')
        with open(table_path, 'r') as file:
            file_bytes = file.read().encode('utf-8')
        files_list.append({'description': label,
                           'fileText': file_bytes})

df = ingress.the_ingress_procedure(files_list)

print(df.columns)

df['placement_type'] = df['PLACE'].apply(ingress.categorize_placement)

date_df = ingress.get_daily_data(df)

print('placement time series')
print(date_df[['date', 'CHILD', 'placement_type', 'DOB', 'new_in', 'last_day', 'transition_tomorrow', 'age_bucket', 'DECOM', 'DEC', 'duration_bucket']].head(10).to_string())

print('Transition time series (first 10 rows)')
print(model.get_raw_placement_transition_data(date_df, bucket_type='age_bucket', freq='1M').head(10).to_string())

print('Transition Matrix, 2019-01-01')
print(model.get_transition_matrix_for_date(date_df, pd.Timestamp('2019-01-01'), bucket_type='age_bucket'))

print('ingress rates, 2018-01-1')
print(model.get_ingress_rates_for_date(date_df, pd.Timestamp('2018-01-01')))
