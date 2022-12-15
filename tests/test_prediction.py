import itertools
from datetime import date

import pandas as pd
import pytest

from cs_demand_model import ModelPredictor
from cs_demand_model.prediction import transition_population


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
            (None, ("Age Bin 1", "PT1")): 0.05,
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
