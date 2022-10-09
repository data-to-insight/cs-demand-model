from pathlib import Path

import pytest
import yaml

import csdmpy.fixtures.config
from csdmpy.config import Config
from csdmpy.config._age_brackets import build_age_brackets

fixtures_file = Path(csdmpy.fixtures.config.__file__).parent / "standard-v1.yaml"


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def AgeBrackets(config):
    return config.AgeBrackets


def test_ages():
    AgeBrackets = build_age_brackets(dict(CAT_A=dict(min=5, max=10)))
    assert AgeBrackets.CAT_A.start == 5
    assert AgeBrackets.CAT_A.end == 10
    assert AgeBrackets.CAT_A.label == "5 to 10"


def test_bracket_for():
    AgeBrackets = build_age_brackets(
        dict(
            CAT_A=dict(min=5, max=10),
            CAT_B=dict(min=10, max=15),
        )
    )

    assert AgeBrackets.bracket_for_age(5) == AgeBrackets.CAT_A
    assert AgeBrackets.bracket_for_age(9) == AgeBrackets.CAT_A
    assert AgeBrackets.bracket_for_age(10) == AgeBrackets.CAT_B


def test_label():
    AgeBrackets = build_age_brackets(
        dict(
            CAT_A=dict(min=5, max=10),
            CAT_B=dict(max=15, label="Birth to 15"),
        )
    )

    assert AgeBrackets.CAT_A.label == "5 to 10"
    assert AgeBrackets.CAT_B.label == "Birth to 15"


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
