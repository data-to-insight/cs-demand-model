import tempfile
from pathlib import Path
from typing import Iterable, List, Mapping

from rpc_wrap import RpcApp

from cs_demand_model import (
    Config,
    DemandModellingDataContainer,
    ModelPredictor,
    PopulationStats,
    fs_datastore,
)

app = RpcApp("CS Demand Model")


class DemandModellingSession:
    def __init__(self):
        self.temp_folder = tempfile.TemporaryDirectory()
        self.temp_folder_path = Path(self.temp_folder.name)
        self.uploads_path = self.temp_folder_path / "uploads"
        self.uploads_path.mkdir(parents=True, exist_ok=True)

        self.config = Config()

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
            folder_path = self.uploads_path / year
            folder_path.mkdir(parents=True, exist_ok=True)
            with open(folder_path / file.filename, "wb") as f:
                f.write(file.read())
        self.datastore_invalidate()

    def delete_files(self, names: Iterable[str]):
        for name in names:
            (self.uploads_path / name).unlink()

    @property
    def datastore(self):
        if self.__datastore is None:
            self.__datastore = fs_datastore(self.uploads_path.as_posix())
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

    def predict(self, start_date, end_date, steps, step_days):
        predictor = ModelPredictor.from_model(
            self.population_stats, start_date, end_date
        )
        self.__prediction = predictor.predict(steps, step_days=step_days)
        return self.__prediction

    def close(self):
        self.datastore_invalidate()
        self.temp_folder.cleanup()


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
def delete_files(names: Iterable[str]) -> List[str]:
    dm_session.delete_files(names)
    return list_files()


@app.call
def population_stats():
    stats = dm_session.population_stats

    return {
        "min_date": stats.stock.index.min(),
        "max_date": stats.stock.index.max(),
    }
