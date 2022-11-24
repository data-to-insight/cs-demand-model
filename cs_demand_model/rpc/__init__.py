import json
import tempfile
import zipfile
from datetime import date
from io import BytesIO
from math import ceil
from pathlib import Path
from typing import Iterable, List

import plotly.express as px
import plotly.graph_objects as go
from dateutil.parser import parse as parse_date
from plotly.subplots import make_subplots
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
        print("Returning datastore", self.__datastore)
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
        print("Returning population stats", self.__population_stats)
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
    stock = stats.stock
    return {
        "minDate": _to_date(stock.index.min()),
        "maxDate": _to_date(stock.index.max()),
    }


@app.call
def predict(
    history_start,
    history_end,
    reference_start,
    reference_end,
    forecast_end,
    step_days,
):
    reference_start = parse_date(reference_start)
    reference_end = parse_date(reference_end)
    forecast_end = parse_date(forecast_end)

    stats = dm_session.population_stats
    predictor = ModelPredictor.from_model(stats, reference_start, reference_end)

    steps = (forecast_end - reference_end).days / step_days
    steps = ceil(steps)
    predicted_pop = predictor.predict(steps, step_days=step_days)
    stock, predicted_pop = stats.stock.align(predicted_pop, axis=1)

    stock_by_type = stock.fillna(0).groupby(level=1, axis=1).sum()
    pred_by_type = predicted_pop.fillna(0).groupby(level=1, axis=1).sum()

    fig = make_subplots()
    for cat, col in dm_session.colors.items():
        fig.add_trace(
            go.Scatter(
                x=stock_by_type.index,
                y=stock_by_type[cat],
                mode="lines",
                name=cat.label,
                line=col,
            )
        )

    for cat, col in dm_session.colors.items():
        fig.add_trace(
            go.Scatter(
                x=pred_by_type.index,
                y=pred_by_type[cat],
                mode="lines",
                showlegend=False,
                line=dict(**col, dash="dash"),
            )
        )

    fig.add_vline(x=reference_end, line_color=px.colors.qualitative.D3[0])
    fig.add_vrect(
        x0=reference_start,
        x1=reference_end,
        line_width=0,
        fillcolor=px.colors.qualitative.D3[0],
        opacity=0.2,
    )

    fig.update_layout(
        yaxis_title="Child Count",
        xaxis_title="Date",
    )

    return json.loads(fig.to_json())


def _to_date(value: date):
    return value.strftime("%Y-%m-%d")
