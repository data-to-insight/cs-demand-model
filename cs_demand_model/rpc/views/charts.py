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
from cs_demand_model.rpc.forms.adjustments import AdjustmentsForm
from cs_demand_model.rpc.forms.cost_proportions import CostProportionsForm
from cs_demand_model.rpc.forms.costs import CostsForm
from cs_demand_model.rpc.state import DemandModellingState
from cs_demand_model.rpc.util import parse_date


def _to_float(value, default=None):
    try:
        if value is None:
            return default
        elif isinstance(value, str) and value.strip() == "":
            return default
        else:
            return float(value)
    except:
        return default


def _to_int(value, default=None):
    try:
        if value is None:
            return default
        elif isinstance(value, str) and value.strip() == "":
            return default
        else:
            return int(value)
    except:
        return default


class ChartsView:
    def action(self, action, state: DemandModellingState, data):
        if action == "calculate":
            state.start_date = parse_date(data["start_date"])
            state.end_date = parse_date(data["end_date"])
            state.prediction_start_date = parse_date(data["prediction_start_date"])
            state.prediction_end_date = parse_date(data["prediction_end_date"])
            state.step_days = _to_int(data["step_size"])
            state.chart_filter = data.get("chart_filter", "")
            for key, value in data.items():
                if key.startswith("costs_"):
                    state.costs[key] = _to_float(value)
                elif key.startswith("cost_proportions_"):
                    state.cost_proportions[key] = _to_float(value)
                elif key.startswith("adjustments|"):
                    state.adjustments[key] = _to_float(value)

        elif action == "reset":
            state = DemandModellingState()
        return state

    def render(self, state: DemandModellingState):
        main = [
            Select(
                id="chart_filter",
                title="Filters",
                options=[dict(value="all", label="All")]
                + [dict(value=a.name, label=a.label) for a in state.config.AgeBrackets],
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
        ]

        if state.prediction_adjusted is not None:
            main += [
                Paragraph(
                    "The adjustments chart shows the difference between the original forecast and the adjusted "
                    "forecast. "
                ),
                Chart(
                    state,
                    figs.forecast,
                    render_args=dict(
                        title="Population forecast (adjusted)",
                        prediction=state.prediction_adjusted,
                    ),
                    id="adj-forecast",
                ),
                Chart(
                    state,
                    figs.costs,
                    render_args=dict(
                        title="Costs forecast (adjusted)",
                        prediction=state.prediction_adjusted,
                    ),
                    id="adj-costs",
                ),
            ]

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
                Expando(
                    AdjustmentsForm(state),
                    ButtonBar(Button("Calculate Now", action="calculate")),
                    title="Add Hypothetical Transfers",
                    id="adjustments_expando",
                ),
            ],
            main=main,
            id="charts_view",
        )
