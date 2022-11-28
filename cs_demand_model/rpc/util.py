from datetime import date
from typing import Mapping

from dateutil.parser import parse as dateutil_parse


def format_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def parse_date(value: str) -> date:
    return dateutil_parse(value, dayfirst=True)


def convert_date(value: Mapping[str, str]) -> date:
    return dateutil_parse(
        f"{value['day']} {value['month']} {value['year']}", dayfirst=True
    )
