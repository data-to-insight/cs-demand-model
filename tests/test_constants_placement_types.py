from csdmpy.constants import PlacementType, PlacementCategory


def test_getitem():
    assert PlacementType['H5'] == PlacementType.H5
    assert PlacementType['P1'] == PlacementType.P1
    assert PlacementType['XX'] == PlacementType.OTHER

    assert PlacementType['XX'].value.value == PlacementCategory.OTHER
