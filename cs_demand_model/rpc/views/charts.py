from cs_demand_model.rpc import figs
from cs_demand_model.rpc.components import (
    Button,
    ButtonBar,
    Chart,
    Expando,
    Paragraph,
    Select,
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
            state.chart_filter = data.get("chart_filter", "")
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
                Select(
                    id="chart_filter",
                    title="Filters",
                    options=[dict(value="all", label="All")]
                    + [
                        dict(value=a.name, label=a.label)
                        for a in state.config.AgeBrackets
                    ],
                    auto_action="calculate",
                ),
                Chart(state, figs.forecast, id="forecast"),
                Chart(state, figs.costs, id="costs"),
                Paragraph(
                    "The light box denotes the period for which the model has been trained, and the dark blue "
                    "line is the start date for the prediction."
                ),
                Paragraph(
                    "Use the drop-down above the chart to filter by age. Individual series can be toggled by "
                    "clicking the legend in the chart."
                ),
                Paragraph(
                    "You can hover over individual series in the chart to see the exact values.",
                ),
            ],
            id="charts_view",
        )
