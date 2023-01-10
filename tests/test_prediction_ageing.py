from datetime import date

import pandas as pd
import pytest

from cs_demand_model import Config, ModelPredictor
from cs_demand_model.prediction import ageing_out, combine_rates


@pytest.fixture
def config():
    return Config()


def test_combine_rates(config):
    rates_1 = pd.Series(
        [0.1, 0.2, 0.3],
        index=pd.MultiIndex.from_tuples([("T", "A"), ("T", "B"), ("T", "C")]),
    )
    rates_2 = pd.Series(
        [0.4, 0.2, 0.3],
        index=pd.MultiIndex.from_tuples([("T", "D"), ("T", "B"), ("T", "C")]),
    )
    combined = combine_rates(rates_1, rates_2)
    assert combined[("T", "A")] == pytest.approx(0.1, abs=0.1)
    assert combined[("T", "B")] == pytest.approx(0.4, abs=0.1)
    assert combined[("T", "C")] == pytest.approx(0.6, abs=0.1)
    assert combined[("T", "D")] == pytest.approx(0.4, abs=0.1)


def assert_populations(config, population, category, *expected, check_sum=True):
    index = [
        (age_bracket.name, category)
        for age_bracket in list(config.AgeBrackets)[: len(expected)]
    ]
    assert population[index].values.tolist() == [
        pytest.approx(v, abs=0.1) for v in expected
    ]
    if check_sum:
        assert population[index].sum() == pytest.approx(100, abs=0.1)


def test_ageing(config):
    age_brackets = list(config.AgeBrackets)
    AB1 = age_brackets[0].name
    AB2 = age_brackets[1].name
    AB3 = age_brackets[2].name
    AB4 = age_brackets[3].name
    AB5 = age_brackets[4].name

    FOSTERING = config.PlacementCategories.FOSTERING.name
    RESIDENTIAL = config.PlacementCategories.RESIDENTIAL.name

    age_out_rates = ageing_out(config)

    predictor = ModelPredictor(
        population=pd.Series(
            [100, 0, 0, 200, 0, 0],
            index=[
                (AB1, FOSTERING),
                (AB2, FOSTERING),
                (AB3, FOSTERING),
                (AB1, RESIDENTIAL),
                (AB2, RESIDENTIAL),
                (AB3, RESIDENTIAL),
            ],
        ),
        transition_rates=age_out_rates,
        start_date=date(2020, 1, 1),
    )
    predictions = predictor.predict(365)
    next_pop = predictions.iloc[0]
    assert_populations(config, next_pop, FOSTERING, 99.7, 0.3)

    next_pop = predictions.iloc[1]
    assert_populations(config, next_pop, FOSTERING, 99.5, 0.5)

    next_pop = predictions.iloc[2]
    assert_populations(config, next_pop, FOSTERING, 99.2, 0.8)

    next_pop = predictions.iloc[3]
    assert_populations(config, next_pop, FOSTERING, 99.0, 1.0)

    next_pop = predictions.iloc[29]
    assert_populations(config, next_pop, FOSTERING, 92.1, 7.8, 0.1)

    next_pop = predictions.iloc[89]
    assert_populations(config, next_pop, FOSTERING, 78.1, 21.2, 0.7)

    next_pop = predictions.iloc[-1]
    assert_populations(config, next_pop, FOSTERING, 36.7, 54.8, 7.8, 0.6)

    # Now test with step size
    predictions = predictor.predict(12, step_days=30)
    next_pop = predictions.iloc[0]
    assert_populations(config, next_pop, FOSTERING, 92.1, 7.9, 0)

    next_pop = predictions.iloc[2]
    assert_populations(config, next_pop, FOSTERING, 78.1, 21.4, 0.5)

    next_pop = predictions.iloc[-1]
    assert_populations(config, next_pop, FOSTERING, 37.2, 55.1, 7.2, 0.4)
