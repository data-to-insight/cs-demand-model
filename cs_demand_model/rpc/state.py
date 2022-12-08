import inspect
import tempfile
from datetime import date
from functools import lru_cache
from math import ceil
from pathlib import Path
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta
from rpc_wrap.__api import RemoteFile

from cs_demand_model import (
    Config,
    DemandModellingDataContainer,
    ModelPredictor,
    PopulationStats,
    fs_datastore,
)
from cs_demand_model.datastore import DataStore


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
    def __init__(self):
        self.config = Config()
        self.colors = {
            self.config.PlacementCategories.FOSTERING: dict(color="blue"),
            self.config.PlacementCategories.RESIDENTIAL: dict(color="green"),
            self.config.PlacementCategories.SUPPORTED: dict(color="red"),
            self.config.PlacementCategories.OTHER: dict(color="orange"),
        }
        self.__temp_folder = tempfile.TemporaryDirectory()
        self.__temp_folder_path = Path(self.__temp_folder.name)

        self.datastore_ready = False
        self.__datastore = None
        self.step_days = 90

        self.__start_date: Optional[date] = None
        self.__end_date: Optional[date] = None
        self.__prediction_end_date: Optional[date] = None
        self.__predictor: Optional[ModelPredictor] = None

    @state_property(cache=1)
    def datastore(self, datastore_ready) -> Optional[DataStore]:
        if not datastore_ready:
            return None
        if self.__datastore is None:
            self.__datastore = fs_datastore(self.__temp_folder_path.as_posix())
        return self.__datastore

    @datastore.setter
    def datastore(self, value):
        self.__datastore = value
        self.datastore_ready = True

    def add_file(self, id, record):
        file = record["file"]
        if isinstance(file, RemoteFile):
            file_path = self.__temp_folder_path / f"{id}.csv"
            with file_path.open("wb") as f:
                f.write(file.read())

    @property
    def files(self):
        return {
            f.name: dict(
                file=dict(name=f.name.rsplit("_", 2)[0], size=f.stat().st_size)
            )
            for f in self.__temp_folder_path.iterdir()
        }

    @state_property(cache=1)
    def datacontainer(
        self, config: Config, datastore: DataStore, datastore_ready: bool
    ) -> Optional[DemandModellingDataContainer]:
        if not datastore_ready:
            return None
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
    def start_date(self) -> Optional[date]:
        if self.__start_date:
            return self.__start_date
        elif self.date_defaults:
            return self.date_defaults["start_date"]
        else:
            return None

    @start_date.setter
    def start_date(self, value: date):
        self.__start_date = value

    @property
    def end_date(self) -> Optional[date]:
        if self.__end_date:
            return self.__end_date
        elif self.date_defaults:
            return self.date_defaults["end_date"]
        else:
            return None

    @end_date.setter
    def end_date(self, value: date):
        self.__end_date = value

    @property
    def prediction_end_date(self) -> Optional[date]:
        if self.__prediction_end_date:
            return self.__prediction_end_date
        elif self.date_defaults:
            return self.date_defaults["prediction_end_date"]
        else:
            return None

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
