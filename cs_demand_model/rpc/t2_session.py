import inspect
from datetime import date
from functools import lru_cache
from math import ceil
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from cs_demand_model import (
    Config,
    DemandModellingDataContainer,
    ModelPredictor,
    PopulationStats,
)
from cs_demand_model.datastore import DataStore
from cs_demand_model.rpc import charts
from cs_demand_model.rpc.t2.components import (
    BoxPage,
    Button,
    ButtonBar,
    Chart,
    Paragraph,
    SidebarPage,
)
from cs_demand_model.rpc.util import parse_date
from cs_demand_model_samples import V1


def state_property(*dec_args, **dec_kwargs):
    def decorator(func):
        signature = inspect.signature(func)
        param_list = list(signature.parameters.values())[1:]

        if dec_kwargs.get("cache", 0):
            func = lru_cache(maxsize=int(dec_kwargs["cache"]))(func)

        def wrapper(state):
            args = []
            for param in param_list:
                state_value = getattr(state, param.name)
                if state_value is None:
                    return None
                args.append(state_value)
            return func(state, *args)

        return property(wrapper)

    if len(dec_args) == 1 and not dec_kwargs and callable(dec_args[0]):
        return decorator(dec_args[0])
    else:
        return decorator


class DemandModellingState:
    datastore: DataStore = None
    step_days = 90

    def __init__(self):
        self.config = Config()
        self.colors = {
            self.config.PlacementCategories.FOSTERING: dict(color="blue"),
            self.config.PlacementCategories.RESIDENTIAL: dict(color="green"),
            self.config.PlacementCategories.SUPPORTED: dict(color="red"),
            self.config.PlacementCategories.OTHER: dict(color="orange"),
        }
        self.__start_date: Optional[date] = None
        self.__end_date: Optional[date] = None
        self.__prediction_end_date: Optional[date] = None
        self.__predictor: Optional[ModelPredictor] = None

    @state_property(cache=1)
    def datacontainer(
        self, config: Config, datastore: DataStore
    ) -> DemandModellingDataContainer:
        return DemandModellingDataContainer(datastore, config)

    @state_property(cache=1)
    def population_stats(
        self, config: Config, datacontainer: DemandModellingDataContainer
    ) -> PopulationStats:
        return PopulationStats(datacontainer.enriched_view, config)

    @state_property(cache=1)
    def date_defaults(self, population_stats: PopulationStats):
        end_date = population_stats.stock.index.max().date()
        return dict(
            start_date=end_date - relativedelta(years=1),
            end_date=end_date,
            prediction_end_date=end_date + relativedelta(months=18),
        )

    @property
    def start_date(self) -> date:
        return self.__start_date or self.date_defaults["start_date"]

    @start_date.setter
    def start_date(self, value: date):
        self.__start_date = value

    @property
    def end_date(self) -> date:
        return self.__end_date or self.date_defaults["end_date"]

    @end_date.setter
    def end_date(self, value: date):
        self.__end_date = value

    @property
    def prediction_end_date(self) -> date:
        return self.__prediction_end_date or self.date_defaults["prediction_end_date"]

    @prediction_end_date.setter
    def prediction_end_date(self, value: date):
        self.__prediction_end_date = value

    @state_property(cache=1)
    def predictor(self, population_stats, start_date, end_date) -> ModelPredictor:
        return ModelPredictor.from_model(population_stats, start_date, end_date)

    @property
    def steps(self) -> int:
        return ceil((self.prediction_end_date - self.end_date).days / self.step_days)

    @state_property(cache=1)
    def prediction(
        self, predictor: ModelPredictor, steps: int, step_days: int
    ) -> pd.DataFrame:
        return predictor.predict(steps, step_days)


class DataStoreView:
    def action(self, action, state: DemandModellingState, data):
        """
        This is called whenever an action is triggered for this view
        """
        if action == "use_sample_files":
            state.datastore = V1.datastore

    def render(self, state: DemandModellingState):
        return BoxPage(
            Paragraph(
                "This tool automatically forecasts demand for children’s services "
                "placements so that commissioners can conduct sufficiency analyses, "
                "secure appropriate budgets for services and demonstrate the business "
                "case for a new or changed service."
            ),
            Paragraph(
                "Load your local authority’s historic statutory return files on looked "
                "after children (SSDA903 files) to quickly see estimates of future "
                "demand for residential, fostering and supported accommodation "
                "placements."
            ),
            Paragraph(
                "Adjust population and cost parameters to model changes you are "
                "considering, such as the creation of in-house provision, or a "
                "step-down service."
            ),
            Paragraph(
                "Note: You do not need data sharing agreements to use this tool. "
                "Even though it opens in your web-browser, the tool runs offline, "
                "locally on your computer so that none of the data you enter leaves "
                "your device."
            ),
            Paragraph(
                "Drop your SSDA903 return files in below to begin generating forecasts!"
            ),
            ButtonBar(Button("Use sample files", action="use_sample_files")),
        )


class ChartsView:
    def action(self, action, state: DemandModellingState, data):
        if action == "update":
            state.start_date = parse_date(data["start_date"])
            state.end_date = parse_date(data["end_date"])
        return state

    def render(self, state: DemandModellingState):
        return SidebarPage(
            sidebar=[],
            main=[
                Paragraph(
                    "Drop your SSDA903 return files in below to begin generating forecasts!"
                ),
                Chart(state, charts.stock_chart),
            ],
        )


class T2DemandModellingSession:
    def __init__(self):
        self.state = DemandModellingState()
        self.views = {
            "datastore": DataStoreView(),
            "charts": ChartsView(),
        }

    @property
    def current_view(self):
        if self.state.datastore is None:
            return self.views["datastore"]
        else:
            return self.views["charts"]

    def action(self, action, data=None):
        if action != "init":
            self.current_view.action(action, self.state, data)
        return dict(view=self.current_view.render(self.state), state={})
