import itertools
from datetime import date

import pandas as pd
import pytest

from cs_demand_model.prediction import ModelPredictor, ageing_out, transition_population


def test_single_transitions():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2"]
    index_values = list(itertools.product(age_bins, placement_types))
    initial_population = pd.Series([100, 0], index=index_values)
    transition_rates = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
            (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
        }
    )

    next_pop = transition_population(
        initial_population,
        transition_rates=transition_rates,
    )

    assert next_pop[("Age Bin 1", "PT1")] == 100
    assert next_pop[("Age Bin 1", "PT2")] == 0


def test_predictor_steady_state():
    predictor = ModelPredictor(
        population=pd.Series(
            [100, 0], index=[("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")]
        ),
        transition_rates=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        transition_numbers=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        start_date=date(2020, 1, 1),
    )
    predictions = predictor.predict(25)

    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 100
    assert next_pop[("Age Bin 1", "PT2")] == 0

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == 100
    assert last_pop[("Age Bin 1", "PT2")] == 0


def test_predictor_single_rate():
    predictor = ModelPredictor(
        population=pd.Series(
            [100, 0], index=[("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")]
        ),
        transition_rates=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.1,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        transition_numbers=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        start_date=date(2020, 1, 1),
    )
    predictions = predictor.predict(25)

    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 90
    assert next_pop[("Age Bin 1", "PT2")] == 10

    next_pop = predictions.iloc[1]
    assert next_pop[("Age Bin 1", "PT1")] == 81
    assert next_pop[("Age Bin 1", "PT2")] == 19

    next_pop = predictions.iloc[4]
    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(59.0, abs=0.1)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(41.0, abs=0.1)

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == pytest.approx(7.2, abs=0.1)
    assert last_pop[("Age Bin 1", "PT2")] == pytest.approx(92.8, abs=0.1)

    # Now test with step size
    predictions = predictor.predict(5, step_days=5)
    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(59.0, abs=0.1)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(41.0, abs=0.1)

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == pytest.approx(7.2, abs=0.1)
    assert last_pop[("Age Bin 1", "PT2")] == pytest.approx(92.8, abs=0.1)


def test_predictor_complex_rate():
    predictor = ModelPredictor(
        population=pd.Series(
            [100, 0], index=[("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")]
        ),
        transition_rates=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.1,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.05,
            }
        ),
        transition_numbers=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        start_date=date(2020, 1, 1),
    )
    predictions = predictor.predict(25)

    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 90
    assert next_pop[("Age Bin 1", "PT2")] == 10

    next_pop = predictions.iloc[1]
    assert next_pop[("Age Bin 1", "PT1")] == 81.5
    assert next_pop[("Age Bin 1", "PT2")] == 18.5

    next_pop = predictions.iloc[4]
    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(62.9, abs=0.1)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(37.1, abs=0.1)

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == pytest.approx(34.5, abs=0.1)
    assert last_pop[("Age Bin 1", "PT2")] == pytest.approx(65.5, abs=0.1)

    # Now test with step size - these should be similar to the above,
    # but will obviously have a slightly "lower resolution"
    predictions = predictor.predict(5, step_days=5)
    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(59.0, abs=0.1)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(41.0, abs=0.1)

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == pytest.approx(36.0, abs=0.1)
    assert last_pop[("Age Bin 1", "PT2")] == pytest.approx(64.0, abs=0.1)


def test_predictor_single_adjustment():
    predictor = ModelPredictor(
        population=pd.Series(
            [100, 0], index=[("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")]
        ),
        transition_rates=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        transition_numbers=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 10.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        start_date=date(2020, 1, 1),
    )
    predictions = predictor.predict(25)

    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 90
    assert next_pop[("Age Bin 1", "PT2")] == 10

    next_pop = predictions.iloc[1]
    assert next_pop[("Age Bin 1", "PT1")] == 80
    assert next_pop[("Age Bin 1", "PT2")] == 20

    next_pop = predictions.iloc[4]
    assert next_pop[("Age Bin 1", "PT1")] == 50
    assert next_pop[("Age Bin 1", "PT2")] == 50

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == 0
    assert last_pop[("Age Bin 1", "PT2")] == 100

    # Now test with step size
    predictions = predictor.predict(5, step_days=5)
    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 50
    assert next_pop[("Age Bin 1", "PT2")] == 50

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == 0
    assert last_pop[("Age Bin 1", "PT2")] == 100


def test_predictor_complex_adjustment():
    predictor = ModelPredictor(
        population=pd.Series(
            [100, 0], index=[("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")]
        ),
        transition_rates=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0,
            }
        ),
        transition_numbers=pd.Series(
            {
                (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 10,
                (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 5,
            }
        ),
        start_date=date(2020, 1, 1),
    )
    predictions = predictor.predict(25)

    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 90
    assert next_pop[("Age Bin 1", "PT2")] == 10

    next_pop = predictions.iloc[1]
    assert next_pop[("Age Bin 1", "PT1")] == 85
    assert next_pop[("Age Bin 1", "PT2")] == 15

    next_pop = predictions.iloc[4]
    assert next_pop[("Age Bin 1", "PT1")] == 70
    assert next_pop[("Age Bin 1", "PT2")] == 30

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == 5
    assert last_pop[("Age Bin 1", "PT2")] == 95

    # Now test with step size - these should be similar to the above,
    # however the errors are much larger due to the 'probability' only being calculated every 5 days
    predictions = predictor.predict(5, step_days=5)
    next_pop = predictions.iloc[0]
    assert next_pop[("Age Bin 1", "PT1")] == 50
    assert next_pop[("Age Bin 1", "PT2")] == 50

    last_pop = predictions.iloc[-1]
    assert last_pop[("Age Bin 1", "PT1")] == 25
    assert last_pop[("Age Bin 1", "PT2")] == 75


def test_transition_rates():
    age_bins = ["Age Bin 1", "Age Bin 2"]
    placement_types = ["PT1", "PT2", "PT3"]
    index_values = list(itertools.product(age_bins, placement_types))
    initial_population = pd.Series([100, 200, 300, 400, 500, 600], index=index_values)
    transition_rates = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.3,
            (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.1,
            (("Age Bin 1", "PT2"), ("Age Bin 1", "PT3")): 0.1,
            (("Age Bin 1", "PT3"), ("Age Bin 1", "PT1")): 0.05,
        }
    )

    next_pop = transition_population(
        initial_population,
        transition_rates=transition_rates,
    )

    assert next_pop[("Age Bin 1", "PT1")] == 105
    assert next_pop[("Age Bin 1", "PT2")] == 190
    assert next_pop[("Age Bin 1", "PT3")] == 305

    assert initial_population.sum() == next_pop.sum()


def test_transition_repeated():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([100, 0], index=index_values)
    transition_rates = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.1,
        }
    )

    next_pop = initial_population.copy()
    days = [initial_population]
    for ix in range(10):
        next_pop = transition_population(
            next_pop,
            transition_rates=transition_rates,
        )
        days.append(next_pop)

    pt1 = [round(day[("Age Bin 1", "PT1")]) for day in days]
    pt2 = [round(day[("Age Bin 1", "PT2")]) for day in days]

    assert pt1 == [100, 90, 81, 73, 66, 59, 53, 48, 43, 39, 35]
    assert pt2 == [0, 10, 19, 27, 34, 41, 47, 52, 57, 61, 65]

    assert initial_population.sum() == next_pop.sum()


def test_transition_rates_multi_day():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([100, 0], index=index_values)
    transition_rates = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.1,
        }
    )
    next_pop = transition_population(
        initial_population,
        transition_rates=transition_rates,
        days=10,
    )

    assert initial_population.sum() == next_pop.sum()

    assert round(next_pop[("Age Bin 1", "PT1")]) == 35
    assert round(next_pop[("Age Bin 1", "PT2")]) == 65


def test_transition_rates_complex_multi_day():
    age_bins = ["Age Bin 1", "Age Bin 2"]
    placement_types = ["PT1", "PT2", "PT3"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series(
        [10000, 20000, 30000, 40000, 500, 600], index=index_values
    )
    transition_rates = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.0003,
            (("Age Bin 1", "PT2"), ("Age Bin 1", "PT1")): 0.0001,
            (("Age Bin 1", "PT2"), ("Age Bin 1", "PT3")): 0.0001,
            (("Age Bin 1", "PT3"), ("Age Bin 1", "PT1")): 0.00005,
        }
    )

    days = 30

    brute_force = initial_population.copy()
    for _ in range(days):
        brute_force = transition_population(
            brute_force,
            transition_rates=transition_rates,
        )

    next_pop = transition_population(
        initial_population,
        transition_rates=transition_rates,
        days=days,
    )

    assert round(next_pop[("Age Bin 1", "PT1")]) == round(
        brute_force[("Age Bin 1", "PT1")]
    )
    assert round(next_pop[("Age Bin 1", "PT2")]) == round(
        brute_force[("Age Bin 1", "PT2")]
    )


def test_fixed_transition():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2", "PT3"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([100, 0, 200], index=index_values)
    transition_numbers = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.001,
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT3")): 0.001,
            (("Age Bin 1", "PT3"), ("Age Bin 1", "PT2")): 0.001,
        }
    )

    next_pop = transition_population(
        initial_population,
        transition_numbers=transition_numbers,
    )

    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(99.998, abs=0.0005)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(0.002, abs=0.0005)
    assert next_pop[("Age Bin 1", "PT3")] == pytest.approx(200.0, abs=0.0005)

    assert initial_population.sum() == next_pop.sum()


def test_fixed_transition_in():
    """
    This is the case for new entrants to the system.
    """
    age_bins = ["Age Bin 1", "Age Bin 2"]
    placement_types = ["PT1", "PT2"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([0, 0, 100, 200], index=index_values)
    transition_numbers = pd.Series(
        {
            ((), ("Age Bin 1", "PT1")): 0.087671,
            ((), ("Age Bin 1", "PT2")): 0.002,
            ((), ("Age Bin 2", "PT1")): 0.003,
            ((), ("Age Bin 2", "PT2")): 0.004,
        }
    )

    next_pop = transition_population(
        initial_population,
        transition_numbers=transition_numbers,
    )

    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(0.001, abs=0.0005)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(0.002, abs=0.0005)
    assert next_pop[("Age Bin 2", "PT1")] == pytest.approx(100.003, abs=0.0005)
    assert next_pop[("Age Bin 2", "PT2")] == pytest.approx(200.004, abs=0.0005)


def test_fixed_transition_multi_day():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2", "PT3"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([100, 0, 200], index=index_values)
    transition_numbers = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.001,
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT3")): 0.001,
            (("Age Bin 1", "PT3"), ("Age Bin 1", "PT2")): 0.001,
        }
    )

    next_pop = transition_population(
        initial_population, transition_numbers=transition_numbers, days=10
    )

    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(99.98, abs=0.005)
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(0.02, abs=0.005)
    assert next_pop[("Age Bin 1", "PT3")] == pytest.approx(200.0, abs=0.005)


def test_transfer_in_to_system():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2", "PT3"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([100, 0, 200], index=index_values)
    transition_numbers = pd.Series(
        {
            (tuple(), ("Age Bin 1", "PT1")): 0.05,
        }
    )

    next_pop = transition_population(
        initial_population,
        transition_numbers=transition_numbers,
    )

    assert next_pop[("Age Bin 1", "PT1")] == 100.05
    assert next_pop[("Age Bin 1", "PT2")] == 0
    assert next_pop[("Age Bin 1", "PT3")] == 200

    assert initial_population.sum() != next_pop.sum()

    next_pop = transition_population(
        initial_population, transition_numbers=transition_numbers, days=10
    )

    assert next_pop[("Age Bin 1", "PT1")] == pytest.approx(100.5, abs=0.005)
    assert next_pop[("Age Bin 1", "PT2")] == 0
    assert next_pop[("Age Bin 1", "PT3")] == 200


def test_drain_population():
    age_bins = ["Age Bin 1"]
    placement_types = ["PT1", "PT2", "PT3"]
    index_values = list(itertools.product(age_bins, placement_types))

    initial_population = pd.Series([100, 0, 200], index=index_values)
    transition_rates = pd.Series(
        {
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT2")): 0.6,
            (("Age Bin 1", "PT1"), ("Age Bin 1", "PT3")): 0.7,
        }
    )

    next_pop = transition_population(
        initial_population,
        transition_rates=transition_rates,
    )

    assert next_pop[("Age Bin 1", "PT1")] == 0
    assert next_pop[("Age Bin 1", "PT2")] == pytest.approx(
        46.15, abs=0.01
    )  # Would have expected 60
    assert next_pop[("Age Bin 1", "PT3")] == pytest.approx(
        253.85, abs=0.01
    )  # Would have expected 270
