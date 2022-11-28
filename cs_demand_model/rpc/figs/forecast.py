import json

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def forecast(dm_session, dates):
    prediction = dm_session.predict(
        dates.reference_start, dates.reference_end, dates.steps, dates.step_days
    )

    stats = dm_session.population_stats
    stock, predicted_pop = stats.stock.align(prediction.prediction, axis=1)

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

    fig.add_vline(x=dates.reference_end, line_color=px.colors.qualitative.D3[0])
    fig.add_vrect(
        x0=dates.reference_start,
        x1=dates.reference_end,
        line_width=0,
        fillcolor=px.colors.qualitative.D3[0],
        opacity=0.2,
    )

    fig.update_layout(
        yaxis_title="Child Count",
        xaxis_title="Date",
    )

    return json.loads(fig.to_json())
