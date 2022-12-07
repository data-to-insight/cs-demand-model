import json
from datetime import timedelta
from typing import Iterable, List

from dateutil.relativedelta import relativedelta
from rpc_wrap import RpcApp

from . import figs
from .session import DemandModellingSession
from .t2_session import T2DemandModellingSession
from .types import Dates
from .util import format_date

app = RpcApp("CS Demand Model")

dm_session = T2DemandModellingSession()


class T2Encoder(json.JSONEncoder):
    def default(self, obj):
        try:
            obj = obj.__json__()
        except AttributeError:
            pass
        return obj


def json_response(obj):
    return json.loads(json.dumps(obj, cls=T2Encoder))


@app.call
def reset():
    global dm_session
    dm_session = T2DemandModellingSession()


@app.call
def action(action, data=None):
    return json_response(dm_session.action(action, data))
