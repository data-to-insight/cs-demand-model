from pathlib import Path

import cs_demand_model_samples
from cs_demand_model import Config, DemandModellingDataContainer, fs_datastore
from cs_demand_model.data.ssda903 import SSDA903TableType


def test_data_container():
    samples = Path(cs_demand_model_samples.__file__).parent / "combined"
    datastore = fs_datastore(samples.as_posix())

    assert len(list(datastore.files)) == 10

    container = DemandModellingDataContainer(datastore, Config())

    assert container.first_year == 2018
    assert container.last_year == 2022

    assert len(list(container.get_tables_by_type(SSDA903TableType.HEADER))) == 5
