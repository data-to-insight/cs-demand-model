import functools
from enum import Enum, EnumMeta
from typing import Iterable, Optional, Tuple

from pandas.tseries import offsets


class Constants:
    YEAR_IN_DAYS = 365.24


class EnumWithOther(EnumMeta):
    """
    Creates a metaclass so that this enum[<name>] will ALWAYS return a type, even if the <name> is not defined.

    Any unknown values will return OTHER. OTHER must be defined in the enum or a KeyError will be raised.
    """

    def __getitem__(cls, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            try:
                return cls.OTHER
            except AttributeError:
                raise KeyError(
                    f"Unknown value {name} and no OTHER defined in {cls.__name__}"
                )


class OrderableEnum:
    @property
    def index(self) -> int:
        return list(type(self)).index(self)

    def __lt__(self, other):
        return self.index < other.index


@functools.total_ordering
class PlacementCategory(OrderableEnum, Enum, metaclass=EnumWithOther):
    FOSTER = "Foster"
    RESIDENTIAL = "Resi"
    SUPPORTED = "Supported"
    OTHER = "Other"
    NOT_IN_CARE = "Not in care"


class PlacementSubCategory(OrderableEnum, Enum, metaclass=EnumWithOther):
    FOSTER_FRIEND_RELATIVE = PlacementCategory.FOSTER
    FOSTER_IN_HOUSE = PlacementCategory.FOSTER
    FOSTER_IFA = PlacementCategory.FOSTER
    RESIDENTIAL_IN_HOUSE = PlacementCategory.RESIDENTIAL
    RESIDENTIAL_EXTERNAL = PlacementCategory.RESIDENTIAL
    SUPPORTED = PlacementCategory.SUPPORTED
    OTHER_SECURE_HOME = PlacementCategory.OTHER
    OTHER_PLACED_WITH_FAMILY = PlacementCategory.OTHER
    OTHER = PlacementCategory.OTHER
    NOT_IN_CARE = PlacementCategory.NOT_IN_CARE


class PlacementType(OrderableEnum, Enum, metaclass=EnumWithOther):
    H5 = PlacementSubCategory.SUPPORTED

    K1 = PlacementSubCategory.OTHER_SECURE_HOME
    K2 = PlacementSubCategory.RESIDENTIAL_EXTERNAL

    P1 = PlacementSubCategory.OTHER_PLACED_WITH_FAMILY
    P2 = PlacementSubCategory.SUPPORTED

    R1 = PlacementSubCategory.RESIDENTIAL_IN_HOUSE
    R3 = PlacementSubCategory.OTHER_PLACED_WITH_FAMILY

    U1 = PlacementSubCategory.FOSTER_FRIEND_RELATIVE
    U2 = PlacementSubCategory.FOSTER_FRIEND_RELATIVE
    U3 = PlacementSubCategory.FOSTER_FRIEND_RELATIVE
    U4 = PlacementSubCategory.FOSTER_IN_HOUSE
    U5 = PlacementSubCategory.FOSTER_IN_HOUSE
    U6 = PlacementSubCategory.FOSTER_IFA

    OTHER = PlacementSubCategory.OTHER

    NOT_IN_CARE = PlacementSubCategory.NOT_IN_CARE


class AgeBracket(OrderableEnum, Enum):
    BIRTH_TO_ONE = (-1, 1, (PlacementCategory.FOSTER, PlacementCategory.OTHER))
    ONE_TO_FIVE = (
        1,
        5,
        (
            PlacementCategory.FOSTER,
            PlacementCategory.RESIDENTIAL,
            PlacementCategory.OTHER,
        ),
    )
    FIVE_TO_TEN = (
        5,
        10,
        (
            PlacementCategory.FOSTER,
            PlacementCategory.RESIDENTIAL,
            PlacementCategory.OTHER,
        ),
    )
    TEN_TO_SIXTEEN = (
        10,
        16,
        (
            PlacementCategory.FOSTER,
            PlacementCategory.RESIDENTIAL,
            PlacementCategory.OTHER,
        ),
    )
    SIXTEEN_TO_EIGHTEEN = (
        16,
        18,
        (
            PlacementCategory.FOSTER,
            PlacementCategory.RESIDENTIAL,
            PlacementCategory.SUPPORTED,
            PlacementCategory.OTHER,
        ),
    )

    def __init__(
        self, start: int, end: int, placement_categories: Iterable[PlacementCategory]
    ):
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
        return f"{self.start} to {self.end}"

    @property
    def next(self):
        ix = self._member_names_.index(self.name)
        next_ix = ix + 1
        if next_ix >= len(self._member_names_):
            return None
        return list(type(self))[next_ix]

    @staticmethod
    def bracket_for(age: float) -> Optional["AgeBracket"]:
        for bracket in AgeBracket:
            if bracket.start <= age < bracket.end:
                return bracket
        return None


class IntervalUnit(OrderableEnum, Enum):

    DAY = "days", offsets.Day()
    WEEK = "weeks", offsets.Week()
    MONTH = "months", offsets.MonthEnd()
    YEAR = "years", offsets.YearEnd()

    def __init__(self, label, offset):
        self.__label = label
        self.__offset = offset

    @property
    def label(self) -> str:
        return self.__label

    @property
    def offset(self):
        return self.__offset
