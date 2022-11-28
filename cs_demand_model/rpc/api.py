from datetime import timedelta
from typing import Iterable, List

from dateutil.relativedelta import relativedelta
from rpc_wrap import RpcApp

from . import figs
from .session import DemandModellingSession
from .types import Dates
from .util import format_date

app = RpcApp("CS Demand Model")

dm_session = DemandModellingSession()


@app.call
def reset():
    global dm_session
    dm_session.close()
    dm_session = DemandModellingSession()


@app.call
def list_files() -> List[str]:
    return dm_session.list_files()


@app.call
def add_files(files: Iterable) -> List[str]:
    dm_session.add_files(files)
    return list_files()


@app.call
def sample_files():
    dm_session.sample_datastore()


@app.call
def delete_files(names: Iterable[str]) -> List[str]:
    dm_session.delete_files(names)
    return list_files()


@app.call
def population_stats():
    stats = dm_session.population_stats
    stock = stats.stock
    return {
        "minDate": format_date(stock.index.min()),
        "maxDate": format_date(stock.index.max()),
    }


@app.call
def prepare(**kwargs):
    stock = dm_session.population_stats.stock
    min_date = stock.index.min()
    max_date = stock.index.max()
    return {
        "layout": "main",
        "actions": "predict",
        "components": [
            {
                "type": "subtitle",
                "id": "section1",
                "text": "What period of historical would you like to be shown on the graphs?",
            },
            {"type": "dateInput", "id": "history_start", "label": "History Start date"},
            {"type": "dateInput", "id": "history_end", "label": "History End date"},
            {
                "type": "subtitle",
                "id": "section2",
                "text": "Which period of the historical data should the model learn from?",
            },
            {
                "type": "dateInput",
                "id": "reference_start",
                "label": "Reference Start date",
            },
            {"type": "dateInput", "id": "reference_end", "label": "Reference End date"},
            {
                "type": "subtitle",
                "id": "section3",
                "text": "When should the forecast end?",
            },
            {"type": "dateInput", "id": "forecast_end", "label": "Forecast End date"},
            {"type": "integerInput", "id": "step_size", "label": "Step Size (in days)"},
        ],
        "state": {
            "history_start": format_date(min_date),
            "history_end": format_date(max_date),
            "reference_start": format_date(max_date - relativedelta(years=1)),
            "reference_end": format_date(max_date),
            "forecast_end": format_date(max_date + relativedelta(years=1)),
            "step_size": 10,
        },
    }


@app.call
def predict(**kwargs):
    dates = Dates(kwargs.get("dates", {}))

    # return {
    #     "layout": "sidebar",
    #     "sidebar": {
    #         "components": [
    #             {"type": "expando", "title": "Set Forecast Dates", "components": [
    #                 {"type": "dateInput", "label": "History Start Date", "value": format_date(dates.reference_start)},
    #             ]},
    #         ]
    #     },
    #     "main": {
    #         "title": "Demand Modelling",
    #     }
    #
    # }
    return [
        dict(type="plot", plot=figs.forecast(dm_session, dates)),
        dict(type="plot", plot=figs.placeholder("No cost data available")),
    ]
