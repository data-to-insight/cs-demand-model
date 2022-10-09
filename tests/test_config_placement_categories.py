from pathlib import Path

import pytest
import yaml

import csdmpy.fixtures.config
from csdmpy.config import Config
from csdmpy.config._placement_categories import build_placement_categories

fixtures_file = Path(csdmpy.fixtures.config.__file__).parent / "standard-v1.yaml"


def test_basic():
    PlacementCategories = build_placement_categories(dict(CAT_A={}))
    assert PlacementCategories.CAT_A.label == "Cat_a"
    assert PlacementCategories.CAT_A.placement_types == ()


def test_types():
    PlacementCategories = build_placement_categories(
        dict(TYPED=dict(placement_types=["A", "B"]))
    )
    assert PlacementCategories.TYPED.label == "Typed"
    assert PlacementCategories.TYPED.placement_types == ("A", "B")


def test_label():
    PlacementCategories = build_placement_categories(
        dict(LABEL=dict(label="Hello Boss"))
    )
    assert PlacementCategories.LABEL.label == "Hello Boss"


def test_name():
    PlacementCategories = build_placement_categories(
        dict(LABEL=dict(label="Hello Boss"))
    )
    assert PlacementCategories.LABEL.name == "LABEL"


def test_equality():
    PlacementCategories = build_placement_categories(dict(CAT_A={}, CAT_B={}))
    assert PlacementCategories.CAT_A == PlacementCategories.CAT_A
    assert PlacementCategories.CAT_A != PlacementCategories.CAT_B


def test_item_access():
    PlacementCategories = build_placement_categories(dict(CAT_A={}, CAT_B={}))
    assert PlacementCategories["CAT_A"] == PlacementCategories.CAT_A
    assert PlacementCategories["CAT_B"] == PlacementCategories.CAT_B


def test_by_label():
    PlacementCategories = build_placement_categories(
        dict(CAT_A=dict(label="Cat A"), CAT_B=dict(label="Cat B"))
    )
    assert PlacementCategories.labels["Cat A"] == PlacementCategories.CAT_A


def test_defaults():
    PlacementCategories = build_placement_categories({})
    assert PlacementCategories.OTHER is not None
    assert PlacementCategories.OTHER.label == "Other"

    assert PlacementCategories.NOT_IN_CARE is not None
    assert PlacementCategories.NOT_IN_CARE.label == "Not in care"
