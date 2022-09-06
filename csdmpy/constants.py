from enum import Enum
from typing import Iterable, Tuple, Optional, Union


class Constants:
    YEAR_IN_DAYS = 365.24
    NOT_IN_CARE = 'Not in care'


class PlacementCategory(Enum):
    FOSTER = "Foster"
    RESIDENTIAL = "Resi"
    SUPPORTED = "Supported"
    OTHER = "Other"


class PlacementType(Enum):
    U1 = PlacementCategory.FOSTER
    U2 = PlacementCategory.FOSTER
    U3 = PlacementCategory.FOSTER
    U4 = PlacementCategory.FOSTER
    U5 = PlacementCategory.FOSTER
    U6 = PlacementCategory.FOSTER

    K2 = PlacementCategory.RESIDENTIAL
    R1 = PlacementCategory.RESIDENTIAL

    H5 = PlacementCategory.SUPPORTED
    P2 = PlacementCategory.SUPPORTED

    @classmethod
    def category_by_type(cls, placement_type: Union["PlacementType", str]) -> PlacementCategory:
        try:
            return placement_type.type
        except AttributeError:
            pass

        try:
            return cls[placement_type].value
        except KeyError:
            return PlacementCategory.OTHER


class AgeBracket(Enum):
    BIRTH_TO_ONE = (-1, 1, (PlacementCategory.FOSTER, PlacementCategory.OTHER))
    ONE_TO_FIVE = (1, 5, (PlacementCategory.FOSTER, PlacementCategory.RESIDENTIAL, PlacementCategory.OTHER))
    FIVE_TO_TEN = (5, 10, (PlacementCategory.FOSTER, PlacementCategory.RESIDENTIAL, PlacementCategory.OTHER))
    TEN_TO_SIXTEEN = (10, 16, (PlacementCategory.FOSTER, PlacementCategory.RESIDENTIAL, PlacementCategory.OTHER))
    SIXTEEN_TO_EIGHTEEN = (16, 18, (PlacementCategory.FOSTER, PlacementCategory.RESIDENTIAL, PlacementCategory.SUPPORTED, PlacementCategory.OTHER))

    def __init__(self, start:int, end:int, placement_categories:Iterable[PlacementCategory]):
        self.__start = start
        self.__end = end
        self.__placement_categories = tuple(placement_categories)

    @property
    def start(self) -> int:
        return self.__start

    @property
    def end(self) -> int:
        return self.__end

    @property
    def placement_categories(self) -> Tuple[PlacementCategory]:
        return self.__placement_categories

    @property
    def label(self):
        return f'{self.start} to {self.end}'

    @property
    def next(self):
        ix = self._member_names_.index(self.name)
        next_ix = ix+1
        if next_ix >= len(self._member_names_):
            return None
        return list(type(self))[next_ix]

    @staticmethod
    def bracket_for(age:float) -> Optional['AgeBracket']:
        for bracket in AgeBracket:
            if bracket.start <= age < bracket.end:
                return bracket
        return None
