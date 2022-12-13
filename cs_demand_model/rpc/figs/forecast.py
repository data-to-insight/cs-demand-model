import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from cs_demand_model.rpc.figs.placeholder import placeholder


def get_colors(state: "DemandModellingState") -> dict:
    return {
        state.config.PlacementCategories.FOSTERING: dict(color="blue"),
        state.config.PlacementCategories.RESIDENTIAL: dict(color="green"),
        state.config.PlacementCategories.SUPPORTED: dict(color="red"),
        state.config.PlacementCategories.OTHER: dict(color="orange"),
    }


def forecast(state: "DemandModellingState") -> go.Figure:
    if state.population_stats is None or state.prediction is None:
        return placeholder("No data loaded")

    colors = get_colors(state)

    stock = state.population_stats.stock
    prediction = state.prediction

    if state.chart_filter != "all":
        stock = stock.iloc[
            :,
            stock.columns.get_level_values(0)
            == state.config.AgeBrackets[state.chart_filter],
        ]
        prediction = prediction.iloc[
            :,
            prediction.columns.get_level_values(0)
            == state.config.AgeBrackets[state.chart_filter],
        ]

    stock_by_type = stock.fillna(0).groupby(level=1, axis=1).sum()
    pred_by_type = prediction.fillna(0).groupby(level=1, axis=1).sum()

    fig = make_subplots()
    for cat, col in colors.items():
        if cat in stock_by_type.columns:
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
        if cat in pred_by_type.columns:
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
        title="Population forecast (base)",
        yaxis_title="Child Count",
        xaxis_title="Date",
    )

    return fig
