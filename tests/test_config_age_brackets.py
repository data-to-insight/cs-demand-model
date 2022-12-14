from pathlib import Path

import pytest

import cs_demand_model.fixtures.config
from cs_demand_model.config import Config
from cs_demand_model.config._age_brackets import build_age_brackets

fixtures_file = (
    Path(cs_demand_model.fixtures.config.__file__).parent / "standard-v1.yaml"
)


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def AgeBrackets(config):
    return config.AgeBrackets


def test_order(AgeBrackets):
    assert AgeBrackets.BIRTH_TO_ONE.next == AgeBrackets.ONE_TO_FIVE
    assert AgeBrackets.ONE_TO_FIVE.next == AgeBrackets.FIVE_TO_TEN
    assert AgeBrackets.SIXTEEN_TO_EIGHTEEN.next is None

    assert AgeBrackets.BIRTH_TO_ONE.previous is None
    assert AgeBrackets.ONE_TO_FIVE.previous == AgeBrackets.BIRTH_TO_ONE


def test_placement_categories(config):
    AgeBrackets = config.AgeBrackets
    PlacementCategories = config.PlacementCategories
    assert AgeBrackets.BIRTH_TO_ONE.placement_categories == (
        PlacementCategories.FOSTERING,
        PlacementCategories.OTHER,
    )
