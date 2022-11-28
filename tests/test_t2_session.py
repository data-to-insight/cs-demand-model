from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from cs_demand_model.rpc.t2_session import DemandModellingState
from cs_demand_model_samples import V1


def test_t2_session():
    model = DemandModellingState()

    assert model.prediction.prediction is None

    model.datastore.datastore = V1.datastore

    assert model.prediction.prediction is not None

    sample_data_end_date = date(2022, 3, 27)

    assert model.analysis.start_date == sample_data_end_date - relativedelta(years=1)
    assert model.analysis.end_date == sample_data_end_date
    assert model.prediction.prediction_end_date == sample_data_end_date + relativedelta(
        months=18
    )

    assert model.prediction.prediction.index.min() == sample_data_end_date + timedelta(
        days=model.prediction.step_days
    )
    assert (
        model.prediction.prediction.index.max() - model.prediction.prediction_end_date
    ).days < model.prediction.step_days

    model.analysis.start_date = date(2020, 3, 30)
    model.analysis.end_date = date(2021, 3, 30)
    model.prediction.prediction_end_date = date(2022, 3, 30)

    assert model.prediction.prediction.index.min() == date(2021, 6, 28)
    assert model.prediction.prediction.index.max() == date(2022, 6, 23)

    model.prediction.step_days = 30

    assert model.prediction.prediction.index.min() == date(2021, 4, 29)
    assert model.prediction.prediction.index.max() == date(2022, 4, 24)
