import pytest

from cs_demand_model import Config
from cs_demand_model.rpc.state import Adjustments


def test_adjustments():
    config = Config()
    adj = Adjustments(config)

    adj["adjustments|fostering|residential|ten_to_sixteen"] = 1

    assert adj["adjustments|fostering|residential|ten_to_sixteen"] == 1

    assert adj.keys() == {"adjustments|fostering|residential|ten_to_sixteen"}

    with pytest.raises(KeyError):
        adj["dodo"] = 4

    with pytest.raises(KeyError):
        adj["adjustments|xxx|residential|ten_to_sixteen"] = 4

    assert adj.summary == (("adjustments|fostering|residential|ten_to_sixteen", 1),)


def test_adjustment_rates():
    config = Config()
    adj = Adjustments(config)

    adj["adjustments|fostering|residential|ten_to_sixteen"] = 1
    adj["adjustments|residential|fostering|ten_to_sixteen"] = 2
    adj["adjustments|fostering|residential|sixteen_to_eighteen"] = 3
    adj["adjustments|residential|fostering|sixteen_to_eighteen"] = 4

    rates = adj.transition_rates

    assert rates.shape == (4,)
    assert (
        rates[("TEN_TO_SIXTEEN", "FOSTERING"), ("TEN_TO_SIXTEEN", "RESIDENTIAL")]
        == 1 / 30
    )
    assert (
        rates[("TEN_TO_SIXTEEN", "RESIDENTIAL"), ("TEN_TO_SIXTEEN", "FOSTERING")]
        == 2 / 30
    )
