from cs_demand_model.rpc import figs
from cs_demand_model.rpc.components import (
    Button,
    ButtonBar,
    Chart,
    Expando,
    SidebarPage,
)
from cs_demand_model.rpc.forms import ModelDatesForm
from cs_demand_model.rpc.forms.cost_proportions import CostProportionsForm
from cs_demand_model.rpc.forms.costs import CostsForm
from cs_demand_model.rpc.state import DemandModellingState
from cs_demand_model.rpc.util import parse_date


class ChartsView:
    def action(self, action, state: DemandModellingState, data):
        if action == "calculate":
            state.start_date = parse_date(data["start_date"])
            state.end_date = parse_date(data["end_date"])
            state.prediction_end_date = parse_date(data["prediction_end_date"])
            state.step_days = int(data["step_size"])
            for key, value in data.items():
                if key.startswith("costs_"):
                    state.costs[key] = float(value)
                elif key.startswith("cost_proportions_"):
                    state.cost_proportions[key] = float(value)

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
                Expando(
                    CostsForm(state),
                    ButtonBar(Button("Calculate Now", action="calculate")),
                    title="Enter Placement Costs",
                    id="costs_expando",
                ),
                Expando(
                    CostProportionsForm(state),
                    ButtonBar(Button("Calculate Now", action="calculate")),
                    title="Edit Proportions for Cost Categories",
                    id="cost_proportions_expando",
                ),
            ],
            main=[
                Chart(state, figs.forecast, id="forecast"),
                Chart(state, figs.costs, id="costs"),
            ],
            id="charts_view",
        )
