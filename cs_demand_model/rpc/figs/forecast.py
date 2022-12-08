import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_colors(state: "DemandModellingState") -> dict:
    return {
        state.config.PlacementCategories.FOSTERING: dict(color="blue"),
        state.config.PlacementCategories.RESIDENTIAL: dict(color="green"),
        state.config.PlacementCategories.SUPPORTED: dict(color="red"),
        state.config.PlacementCategories.OTHER: dict(color="orange"),
    }


def forecast(state: "DemandModellingState") -> go.Figure:

    colors = get_colors(state)

    stock_by_type = (
        state.population_stats.stock.fillna(0).groupby(level=1, axis=1).sum()
    )
    pred_by_type = state.prediction.fillna(0).groupby(level=1, axis=1).sum()

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
        yaxis_title="Child Count",
        xaxis_title="Date",
    )

    return fig
