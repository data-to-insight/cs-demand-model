from enum import Enum

from csdmpy.constants import AgeBracket


def test_labels():
    assert AgeBracket.BIRTH_TO_ONE.label == "-1 to 1"
    assert AgeBracket.ONE_TO_FIVE.label == '1 to 5'


def test_next():
    assert AgeBracket.BIRTH_TO_ONE.next == AgeBracket.ONE_TO_FIVE
    assert AgeBracket.ONE_TO_FIVE.next == AgeBracket.FIVE_TO_TEN
    assert AgeBracket.FIVE_TO_TEN.next == AgeBracket.TEN_TO_SIXTEEN
    assert AgeBracket.TEN_TO_SIXTEEN.next == AgeBracket.SIXTEEN_TO_EIGHTEEN
    assert AgeBracket.SIXTEEN_TO_EIGHTEEN.next is None


def test_bracket_for():
    assert AgeBracket.bracket_for(0) == AgeBracket.BIRTH_TO_ONE
    assert AgeBracket.bracket_for(1) == AgeBracket.ONE_TO_FIVE
    assert AgeBracket.bracket_for(5) == AgeBracket.FIVE_TO_TEN
    assert AgeBracket.bracket_for(10) == AgeBracket.TEN_TO_SIXTEEN
    assert AgeBracket.bracket_for(16) == AgeBracket.SIXTEEN_TO_EIGHTEEN
    assert AgeBracket.bracket_for(18) is None
