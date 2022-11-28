import tempfile
import zipfile
from datetime import date
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Iterable, List

from cs_demand_model import (
    Config,
    DemandModellingDataContainer,
    ModelPredictor,
    PopulationStats,
    fs_datastore,
)
from cs_demand_model_samples import V1


class DemandModellingSession:
    def __init__(self):
        self.temp_folder = tempfile.TemporaryDirectory()
        self.temp_folder_path = Path(self.temp_folder.name)
        self.uploads_path = self.temp_folder_path / "uploads"
        self.uploads_path.mkdir(parents=True, exist_ok=True)

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

    def list_files(self) -> List[str]:
        return [
            str(f.relative_to(self.uploads_path)) for f in self.uploads_path.iterdir()
        ]

    def add_files(self, files: Iterable):
        for record in files:
            year = record["year"]
            file = record["file"]
            if file.content_type == "application/zip":
                self.add_zip_file(file)
            else:
                folder_path = self.uploads_path / year
                folder_path.mkdir(parents=True, exist_ok=True)
                with open(folder_path / file.filename, "wb") as f:
                    f.write(file.read())
        self.datastore_invalidate()

    def add_zip_file(self, file):
        bytes = BytesIO(file.read())
        with zipfile.ZipFile(bytes, "r") as zip_ref:
            zip_ref.extractall(self.uploads_path)

    def delete_files(self, names: Iterable[str]):
        for name in names:
            (self.uploads_path / name).unlink()

    @property
    def datastore(self):
        if self.__datastore is None:
            self.__datastore = fs_datastore(self.uploads_path.as_posix())
        return self.__datastore

    def sample_datastore(self):
        self.datastore_invalidate()
        self.__datastore = V1.datastore
        return self.__datastore

    def datastore_invalidate(self):
        self.data_container_invalidate()
        self.__datastore = None

    @property
    def data_container(self):
        if self.__datacontainer is None:
            self.__datacontainer = DemandModellingDataContainer(
                self.datastore, self.config
            )
        print("Returning datacontainer", self.__datacontainer)
        return self.__datacontainer

    def data_container_invalidate(self):
        self.population_stats_invalidate()
        self.__datacontainer = None

    @property
    def population_stats(self):
        if self.__population_stats is None:
            self.__population_stats = PopulationStats(
                self.data_container.enriched_view, self.config
            )
        return self.__population_stats

    def population_stats_invalidate(self):
        self.__prediction = None
        self.__population_stats = None

    @lru_cache(maxsize=10)
    def predict(
        self, start_date: date, end_date: date, steps: int, step_days: int
    ) -> "Prediction":
        return Prediction(self.population_stats, start_date, end_date, steps, step_days)

    def predict_invalidate(self):
        self.predict.cache_clear()

    def close(self):
        self.datastore_invalidate()
        self.temp_folder.cleanup()


class Prediction:
    def __init__(self, stats, start_date, end_date, steps, step_days):
        self.stats = stats
        self.start_date = start_date
        self.end_date = end_date
        self.steps = steps
        self.step_days = step_days

        predictor = ModelPredictor.from_model(stats, start_date, end_date)
        self.prediction = predictor.predict(steps, step_days=step_days)
