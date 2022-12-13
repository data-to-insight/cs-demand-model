from datetime import date

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from cs_demand_model.rpc.figs.forecast import get_colors
from cs_demand_model.rpc.figs.placeholder import placeholder


def costs(state: "DemandModellingState") -> go.Figure:
    if state.population_stats is None or state.prediction is None:
        return placeholder("No data loaded")
    colors = get_colors(state)

    stock_by_type = (
        state.population_stats.stock.fillna(0).groupby(level=1, axis=1).sum()
    )
    pred_by_type = state.prediction.fillna(0).groupby(level=1, axis=1).sum()

    cost_items = state.cost_items
    for cat in cost_items.keys():
        stock_by_type[cat] = stock_by_type[cat] * cost_items[cat]
        pred_by_type[cat] = pred_by_type[cat] * cost_items[cat]

    fig = make_subplots()
    for cat, col in colors.items():
        fig.add_trace(
            go.Scatter(
                x=stock_by_type.index,
                y=stock_by_type[cat],
                mode="lines",
                name=cat.label,
                line=col,
            )
        )

    for cat, col in colors.items():
        fig.add_trace(
            go.Scatter(
                x=pred_by_type.index,
                y=pred_by_type[cat],
                mode="lines",
                showlegend=False,
                line=dict(**col, dash="dash"),
            )
        )

    fig.add_vline(x=state.end_date, line_color=px.colors.qualitative.D3[0])
    fig.add_vrect(
        x0=state.start_date,
        x1=state.end_date,
        line_width=0,
        fillcolor=px.colors.qualitative.D3[0],
        opacity=0.2,
    )

    fig.update_layout(
        yaxis_title="Costs",
        xaxis_title="Date",
    )

    return fig
