import json
import logging
from datetime import date
from typing import Mapping

from dateutil.parser import parse as dateutil_parse

logger = logging.getLogger(__name__)


def format_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def parse_date(value: str) -> date:
    return dateutil_parse(value, dayfirst=True)


def convert_date(value: Mapping[str, str]) -> date:
    return dateutil_parse(
        f"{value['day']} {value['month']} {value['year']}", dayfirst=True
    )


class T2Encoder(json.JSONEncoder):
    def default(self, obj):
        try:
            obj = obj.__json__()
        except AttributeError:
            pass

        try:
            obj = format_date(obj)
        except AttributeError:
            pass

        return obj


def json_response(obj):
    print("Serializing", obj)
    return json.loads(json.dumps(obj, cls=T2Encoder))
