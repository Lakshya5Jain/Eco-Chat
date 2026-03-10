"""Visualization layer — Plotly chart builders for economic data."""

import pandas as pd
import plotly.graph_objects as go

# Distinct color palette for chart traces
COLORS = [
    "#2563EB",  # blue
    "#DC2626",  # red
    "#16A34A",  # green
    "#D97706",  # amber
    "#9333EA",  # purple
    "#0891B2",  # cyan
]

_LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    hovermode="x unified",
    height=450,
    margin=dict(l=60, r=30, t=50, b=50),
    font=dict(size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def line_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
) -> go.Figure:
    """Create a line chart from a DataFrame.

    Parameters
    ----------
    df : DataFrame with a 'date' column and one or more numeric columns.
    title : Chart title.
    y_label : Y-axis label.
    series_columns : Which columns to plot. Defaults to all non-date columns.
    """
    fig = go.Figure()
    cols = series_columns or [c for c in df.columns if c != "date"]

    for i, col in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[col], mode="lines", name=col,
            line=dict(color=COLORS[i % len(COLORS)]),
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_label,
        **_LAYOUT_DEFAULTS,
    )
    return fig


def bar_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
) -> go.Figure:
    """Create a bar chart from a DataFrame."""
    fig = go.Figure()
    cols = series_columns or [c for c in df.columns if c != "date"]

    for i, col in enumerate(cols):
        fig.add_trace(go.Bar(
            x=df["date"], y=df[col], name=col,
            marker_color=COLORS[i % len(COLORS)],
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_label,
        barmode="group",
        **_LAYOUT_DEFAULTS,
    )
    return fig


def multi_series_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
) -> go.Figure:
    """Create a multi-series comparison line chart.

    Identical to line_chart but named explicitly for the agent to signal
    'comparison' intent.
    """
    return line_chart(df, title=title, y_label=y_label, series_columns=series_columns)


def create_chart(
    df: pd.DataFrame,
    chart_type: str = "line",
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
) -> go.Figure:
    """Dispatch to the right chart builder based on *chart_type*.

    Supported types: "line", "bar", "multi_series" / "comparison".
    Falls back to line chart for unknown types.
    """
    chart_type = chart_type.lower().strip()
    builders = {
        "line": line_chart,
        "bar": bar_chart,
        "multi_series": multi_series_chart,
        "comparison": multi_series_chart,
    }
    builder = builders.get(chart_type, line_chart)
    return builder(df, title=title, y_label=y_label, series_columns=series_columns)
