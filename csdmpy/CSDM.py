import pandas as np
import numpy as np
# from model import ...
# from ingress import ...

class CSDM():
    # attributes:
    '''    _raw_data
    _shaped_data

    _populations_time_series
    _transition_time_series
    _transition_probabilities
    _ingress_rates

    _adjustments

    _populations_time_series_forecast
    _populations_time_series_forecast_adjusted
    _cost_estimates
    '''
    def __init__(self, num_samples, start_date, number_days, buckets, ingress_rates, transition_matrix,
               age_out_daily_probs=None):
        pass
