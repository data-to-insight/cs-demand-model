from csdmpy import ingress, model
import pandas as pd

df = ingress.read_combined_903()

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
