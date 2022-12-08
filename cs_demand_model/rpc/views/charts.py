from cs_demand_model.rpc import figs
from cs_demand_model.rpc.components import (
    Button,
    ButtonBar,
    Chart,
    Expando,
    Paragraph,
    SidebarPage,
)
from cs_demand_model.rpc.forms import ModelDatesForm
from cs_demand_model.rpc.state import DemandModellingState
from cs_demand_model.rpc.util import parse_date


class ChartsView:
    def action(self, action, state: DemandModellingState, data):
        print("ACTION", action, data)
        if action == "calculate":
            state.start_date = parse_date(data["start_date"])
            state.end_date = parse_date(data["end_date"])
            state.prediction_end_date = parse_date(data["prediction_end_date"])
            state.step_days = int(data["step_size"])
        elif action == "reset":
            state = DemandModellingState()
        return state

    def render(self, state: DemandModellingState):
        return SidebarPage(
            sidebar=[
                ButtonBar(Button("Start Again", action="reset")),
                Expando(
                    ModelDatesForm(),
                    ButtonBar(Button("Calculate Now", action="calculate")),
                    title="Set Forecast Dates",
                    id="model_dates_expando",
                ),
            ],
            main=[
                Paragraph(
                    "Drop your SSDA903 return files in below to begin generating forecasts!"
                ),
                Chart(state, figs.forecast),
            ],
            id="charts_view",
        )
