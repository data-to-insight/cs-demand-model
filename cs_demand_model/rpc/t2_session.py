from datetime import date
from math import ceil
from typing import Optional

from dateutil.relativedelta import relativedelta

from cs_demand_model import (
    Config,
    DemandModellingDataContainer,
    ModelPredictor,
    PopulationStats,
)
from cs_demand_model.datastore import DataStore
from cs_demand_model.rpc.util import parse_date
from cs_demand_model_samples import V1


class DemandModellingSession:
    def __init__(self):
        self.config = Config()
        self.colors = {
            self.config.PlacementCategories.FOSTERING: dict(color="blue"),
            self.config.PlacementCategories.RESIDENTIAL: dict(color="green"),
            self.config.PlacementCategories.SUPPORTED: dict(color="red"),
            self.config.PlacementCategories.OTHER: dict(color="orange"),
        }
        self.__datastore = None
        self.__datacontainer = None
        self.__population_stats = None
        self.__prediction = None


class DataStoreState:
    """
    The datastore is responsible for storing files and calculating the combined view
    """

    def __init__(self, state: "DemandModellingState"):
        self.__state = state
        self.__config = Config()
        self.__datastore: Optional[DataStore] = None
        self.__datacontainer = None
        self.__population_stats = None

    @property
    def config(self) -> Config:
        return self.__config

    @property
    def datastore(self) -> DataStore:
        return self.__datastore

    @datastore.setter
    def datastore(self, value: DataStore):
        self.__datastore = value
        self.__datacontainer = None
        self.__population_stats = None

    @property
    def datacontainer(self) -> DemandModellingDataContainer:
        if not self.__datacontainer:
            self.calculate()
        return self.__datacontainer

    @property
    def population_stats(self) -> PopulationStats:
        if not self.__population_stats:
            self.calculate()
        return self.__population_stats

    def calculate(self):
        if self.datastore:
            self.__datacontainer = DemandModellingDataContainer(
                self.datastore, self.config
            )
            self.__population_stats = PopulationStats(
                self.__datacontainer.enriched_view, self.config
            )


class AnalysisState:
    """
    The analysis is responsible for calculating the data required for a prediction.
    """

    def __init__(self, state: "DemandModellingState"):
        self.__state = state

        self.__start_date: Optional[date] = None
        self.__end_date: Optional[date] = None
        self.__predictor: Optional[ModelPredictor] = None

    def defaults(self):
        if self.__state.datastore.population_stats:
            self.__end_date = (
                self.__state.datastore.population_stats.stock.index.max().date()
            )
            self.__start_date = self.__end_date - relativedelta(years=1)

    @property
    def start_date(self) -> date:
        if self.__start_date is None:
            self.defaults()
        return self.__start_date

    @start_date.setter
    def start_date(self, value: date):
        self.__start_date = value
        self.__set_predictor(None)

    @property
    def end_date(self) -> date:
        if self.__end_date is None:
            self.defaults()
        return self.__end_date

    @end_date.setter
    def end_date(self, value: date):
        self.__end_date = value
        self.__set_predictor(None)

    @property
    def predictor(self):
        if self.__predictor is None and self.__state.datastore.population_stats:
            self.__set_predictor(
                ModelPredictor.from_model(
                    self.__state.datastore.population_stats,
                    self.start_date,
                    self.end_date,
                )
            )
        return self.__predictor

    def __set_predictor(self, value: Optional[ModelPredictor]):
        self.__predictor = value
        self.__state.prediction.clear()


class PredictionState:
    def __init__(self, state: "DemandModellingState"):
        self.__state = state

        self.__step_days = 90
        self.__prediction_end_date: Optional[date] = None
        self.__prediction = None

    @property
    def step_days(self):
        return self.__step_days

    @step_days.setter
    def step_days(self, value):
        self.__step_days = value
        self.__set_prediction(None)

    @property
    def prediction_end_date(self) -> date:
        if not self.__prediction_end_date:
            self.defaults()
        return self.__prediction_end_date

    @prediction_end_date.setter
    def prediction_end_date(self, value: date):
        self.__prediction_end_date = value
        self.__set_prediction(None)

    @property
    def steps(self) -> int:
        return ceil(
            (self.prediction_end_date - self.__state.analysis.end_date).days
            / self.step_days
        )

    def defaults(self):
        if not self.__prediction_end_date:
            self.__prediction_end_date = self.__state.analysis.end_date + relativedelta(
                months=18
            )

    def clear(self):
        self.__set_prediction(None)

    @property
    def prediction(self):
        if self.__prediction is None and self.__state.analysis.predictor:
            self.__set_prediction(
                self.__state.analysis.predictor.predict(self.steps, self.step_days)
            )
        return self.__prediction

    def __set_prediction(self, prediction):
        self.__prediction = prediction


class DemandModellingState:
    def __init__(self):
        self.datastore = DataStoreState(self)
        self.analysis = AnalysisState(self)
        self.prediction = PredictionState(self)


class DataStoreView:
    def init(self, state: DemandModellingState):
        """
        This is called before each render, so that we can update the state if necessary.
        """
        return state

    def action(self, action, state: DemandModellingState, data):
        """
        This is called whenever an action is triggered for this view
        """
        if action == "use_sample_files":
            state.datastore.datastore = V1.datastore
        return state

    def is_complete(self, state: DemandModellingState):
        """
        This is called prior to rendering the view to determine if this view is complete.
        """
        return state.datastore.datastore is not None

    def render(self):
        return {
            "layout": "main",
            "components": [
                {
                    "type": "paragraph",
                    "text": "This tool automatically forecasts demand for children’s services "
                    "placements so that commissioners can conduct sufficiency analyses, "
                    "secure appropriate budgets for services and demonstrate the business "
                    "case for a new or changed service.",
                },
                {
                    "type": "paragraph",
                    "text": "Load your local authority’s historic statutory return files on looked "
                    "after children (SSDA903 files) to quickly see estimates of future "
                    "demand for residential, fostering and supported accommodation "
                    "placements.",
                },
                {
                    "type": "paragraph",
                    "text": "Adjust population and cost parameters to model changes you are "
                    "considering, such as the creation of in-house provision, or a "
                    "step-down service.",
                },
                {
                    "type": "paragraph",
                    "text": "Note: You do not need data sharing agreements to use this tool. "
                    "Even though it opens in your web-browser, the tool runs offline, "
                    "locally on your computer so that none of the data you enter leaves "
                    "your device.",
                },
                {
                    "type": "paragraph",
                    "text": "Drop your SSDA903 return files in below to begin generating forecasts!",
                },
                {
                    "type": "button",
                    "text": "Use Sample Files",
                    "action": "use_sample_files",
                },
            ],
        }


class DatesView:
    def init(self, state: DemandModellingState):
        """
        This is called before each render, so that we can update the state if necessary.
        """
        return state

    def action(self, action, state: DemandModellingState, data):
        """
        This is called whenever an action is triggered for this view
        """
        if action == "update":
            state.analysis.start_date = parse_date(data["start_date"])
            state.analysis.end_date = parse_date(data["end_date"])
        return state


class PredictionView:
    def init(self, state: DemandModellingState):
        """
        This is called before each render, so that we can update the state if necessary.
        """
        return state

    def action(self, action, state: DemandModellingState, data):
        """
        This is called whenever an action is triggered for this view
        """
        if action == "update":
            state.analysis.start_date = parse_date(data["start_date"])
            state.analysis.end_date = parse_date(data["end_date"])
        return state
