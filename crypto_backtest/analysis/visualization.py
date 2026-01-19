"""Visualization helpers using Plotly."""

from __future__ import annotations

import pandas as pd


def plot_equity_curve(equity_curve: pd.Series):
    """Create an interactive equity curve plot."""
    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError("plotly is required for visualization") from exc

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode="lines",
            name="Equity",
        )
    )
    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Time",
        yaxis_title="Equity",
        template="plotly_white",
    )
    return fig
