import pandas as pd
import matplotlib.pyplot as pp
import csdmpy_fakedata as sample
from csdmpy.datacontainer import DemandModellingDataContainer
from csdmpy.population_stats import PopulationStats
from csdmpy.prediction import ModelFactory

hist_start, ref_start, ref_end, hist_end, pred_end = pd.to_datetime(
    ['2015-01-01', '2019-07-01', '2020-01-01', '2020-01-01', '2021-07-01'])

dc = DemandModellingDataContainer(sample.V1)
stats = PopulationStats(dc.get_enriched_view())

fac = ModelFactory(stats, ref_start, ref_end)
predictor = fac.predictor(ref_end)

prediction_days = (pred_end - ref_end).days

predicted_pop = predictor.predict(prediction_days, progress=True)

historic_pop = stats.stock.loc[hist_start:ref_end]

pd.concat([historic_pop, predicted_pop], axis=0).plot(legend=False)
pp.axvline(hist_end, alpha=0.4)
pp.axvspan(ref_start, ref_end, alpha=0.1)
pp.show()
