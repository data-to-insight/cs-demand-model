import plotly.graph_objects as go


def placeholder(text: str = "Placeholder") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=text, showarrow=False, xref="paper", yref="paper", font_size=28
    )
    fig.update_layout(
        xaxis_visible=False,
        yaxis_visible=False,
    )
    return fig
