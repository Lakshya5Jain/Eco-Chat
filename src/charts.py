"""Visualization layer — Plotly chart builders for economic data.

Supports line, area, bar, and multi-series comparison charts with:
- Dual y-axes when series have different units/scales
- Interactive range slider for time navigation
- Spike lines for cross-series reference
- Rich hover with formatted values and units
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Distinct color palette for chart traces
COLORS = [
    "#0032FF",  # Millennium blue
    "#DC2626",  # red
    "#16A34A",  # green
    "#D97706",  # amber
    "#9333EA",  # purple
    "#0891B2",  # cyan
    "#F43F5E",  # rose
    "#6366F1",  # indigo
]

_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    hovermode="x unified",
    height=480,
    margin=dict(l=60, r=60, t=60, b=50),
    font=dict(size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,10,20,0.5)",
)

_AXIS_DEFAULTS = dict(
    gridcolor="rgba(0,50,255,0.12)",
    showspikes=True,
    spikecolor="rgba(255,255,255,0.3)",
    spikethickness=1,
    spikedash="dot",
    spikemode="across",
)


def _format_hover_value(val: float) -> str:
    """Format a number for hover display."""
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"{val:,.1f}B"
    if abs_val >= 1_000_000:
        return f"{val:,.1f}M"
    if abs_val >= 10_000:
        return f"{val:,.0f}"
    if abs_val >= 100:
        return f"{val:,.1f}"
    if abs_val >= 1:
        return f"{val:,.2f}"
    return f"{val:,.4f}"


def _needs_dual_axis(meta_list: list[dict]) -> bool:
    """Determine if series need dual y-axes based on differing units."""
    if not meta_list or len(meta_list) < 2:
        return False
    units = [m.get("units", "").strip().lower() for m in meta_list]
    # Different non-empty units → dual axis
    unique = set(u for u in units if u)
    return len(unique) >= 2


def _apply_rangeslider(fig: go.Figure) -> None:
    """Add an interactive range slider to the x-axis."""
    fig.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.04),
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=2, label="2Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(label="All", step="all"),
            ],
            bgcolor="rgba(0,50,255,0.15)",
            activecolor="rgba(0,50,255,0.4)",
            font=dict(size=11),
        ),
    )


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def line_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
    meta_list: list[dict] | None = None,
) -> go.Figure:
    """Create a line chart with optional dual y-axes for different units."""
    cols = series_columns or [c for c in df.columns if c != "date"]
    meta_list = meta_list or []
    dual = _needs_dual_axis(meta_list) and len(cols) == 2

    if dual:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = go.Figure()

    for i, col in enumerate(cols):
        secondary = dual and i == 1
        unit = meta_list[i].get("units", "") if i < len(meta_list) else ""
        hover_template = f"<b>{col}</b>: %{{y:,.2f}}"
        if unit:
            hover_template += f" {unit}"
        hover_template += "<extra></extra>"

        trace = go.Scatter(
            x=df["date"],
            y=df[col],
            mode="lines",
            name=meta_list[i].get("title", col) if i < len(meta_list) else col,
            line=dict(color=COLORS[i % len(COLORS)], width=2.5),
            hovertemplate=hover_template,
        )
        if dual:
            fig.add_trace(trace, secondary_y=secondary)
        else:
            fig.add_trace(trace)

    layout_kw = {**_LAYOUT_DEFAULTS, "title": title}
    fig.update_layout(**layout_kw)

    if dual:
        left_unit = meta_list[0].get("units", "") if meta_list else ""
        right_unit = meta_list[1].get("units", "") if len(meta_list) > 1 else ""
        fig.update_yaxes(
            title_text=left_unit, secondary_y=False,
            **_AXIS_DEFAULTS,
        )
        fig.update_yaxes(
            title_text=right_unit, secondary_y=True,
            **_AXIS_DEFAULTS,
        )
    else:
        fig.update_yaxes(title_text=y_label, **_AXIS_DEFAULTS)

    fig.update_xaxes(title_text="Date", **_AXIS_DEFAULTS)
    _apply_rangeslider(fig)
    return fig


def area_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
    meta_list: list[dict] | None = None,
) -> go.Figure:
    """Create an area chart — filled line chart."""
    cols = series_columns or [c for c in df.columns if c != "date"]
    meta_list = meta_list or []
    fig = go.Figure()

    for i, col in enumerate(cols):
        unit = meta_list[i].get("units", "") if i < len(meta_list) else ""
        hover_template = f"<b>{col}</b>: %{{y:,.2f}}"
        if unit:
            hover_template += f" {unit}"
        hover_template += "<extra></extra>"

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[col],
            mode="lines",
            name=meta_list[i].get("title", col) if i < len(meta_list) else col,
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            fill="tozeroy" if i == 0 else "tonexty",
            fillcolor=COLORS[i % len(COLORS)].replace(")", ",0.15)").replace("rgb", "rgba")
            if "rgb" in COLORS[i % len(COLORS)] else None,
            opacity=0.85,
            hovertemplate=hover_template,
        ))

    fig.update_layout(title=title, xaxis_title="Date", yaxis_title=y_label, **_LAYOUT_DEFAULTS)
    fig.update_xaxes(**_AXIS_DEFAULTS)
    fig.update_yaxes(**_AXIS_DEFAULTS)
    _apply_rangeslider(fig)
    return fig


def bar_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
    meta_list: list[dict] | None = None,
) -> go.Figure:
    """Create a bar chart."""
    cols = series_columns or [c for c in df.columns if c != "date"]
    meta_list = meta_list or []
    fig = go.Figure()

    for i, col in enumerate(cols):
        unit = meta_list[i].get("units", "") if i < len(meta_list) else ""
        hover_template = f"<b>{col}</b>: %{{y:,.2f}}"
        if unit:
            hover_template += f" {unit}"
        hover_template += "<extra></extra>"

        fig.add_trace(go.Bar(
            x=df["date"],
            y=df[col],
            name=meta_list[i].get("title", col) if i < len(meta_list) else col,
            marker_color=COLORS[i % len(COLORS)],
            opacity=0.9,
            hovertemplate=hover_template,
        ))

    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title=y_label,
        barmode="group",
        **_LAYOUT_DEFAULTS,
    )
    fig.update_xaxes(**_AXIS_DEFAULTS)
    fig.update_yaxes(**_AXIS_DEFAULTS)
    _apply_rangeslider(fig)
    return fig


def comparison_chart(
    df: pd.DataFrame,
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
    meta_list: list[dict] | None = None,
) -> go.Figure:
    """Multi-series comparison with automatic dual y-axes when units differ.

    For 2 series with different units: dual y-axis layout.
    For 3+ series or same units: shared axis with normalized hover.
    """
    cols = series_columns or [c for c in df.columns if c != "date"]
    meta_list = meta_list or []

    # Dual axis for exactly 2 series with different units
    if len(cols) == 2 and _needs_dual_axis(meta_list):
        return line_chart(df, title=title, series_columns=cols, meta_list=meta_list)

    # 3+ series with different scales: normalize to percentage change from start
    if len(cols) >= 3 and _needs_dual_axis(meta_list):
        return _normalized_comparison(df, title=title, series_columns=cols, meta_list=meta_list)

    # Same units: standard multi-line
    return line_chart(df, title=title, y_label=y_label, series_columns=cols, meta_list=meta_list)


def _normalized_comparison(
    df: pd.DataFrame,
    title: str = "",
    series_columns: list[str] | None = None,
    meta_list: list[dict] | None = None,
) -> go.Figure:
    """Normalize series to % change from first value for apples-to-apples comparison."""
    cols = series_columns or [c for c in df.columns if c != "date"]
    meta_list = meta_list or []
    fig = go.Figure()

    for i, col in enumerate(cols):
        series = df[col].dropna()
        if series.empty:
            continue
        base = series.iloc[0]
        if base == 0:
            normalized = series
        else:
            normalized = ((series - base) / abs(base)) * 100

        label = meta_list[i].get("title", col) if i < len(meta_list) else col
        fig.add_trace(go.Scatter(
            x=df.loc[series.index, "date"],
            y=normalized,
            mode="lines",
            name=label,
            line=dict(color=COLORS[i % len(COLORS)], width=2.5),
            hovertemplate=f"<b>{label}</b>: %{{y:+.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        title=title + " (% change from start)" if title else "Comparison (% change from start)",
        xaxis_title="Date",
        yaxis_title="% Change",
        **_LAYOUT_DEFAULTS,
    )
    fig.update_xaxes(**_AXIS_DEFAULTS)
    fig.update_yaxes(**_AXIS_DEFAULTS, zeroline=True, zerolinecolor="rgba(255,255,255,0.3)")
    _apply_rangeslider(fig)
    return fig


# ---------------------------------------------------------------------------
# Public dispatch
# ---------------------------------------------------------------------------

def create_chart(
    df: pd.DataFrame,
    chart_type: str = "line",
    title: str = "",
    y_label: str = "",
    series_columns: list[str] | None = None,
    meta_list: list[dict] | None = None,
) -> go.Figure:
    """Dispatch to the right chart builder based on *chart_type*.

    Supported types: "line", "area", "bar", "comparison" / "multi_series".
    Falls back to line chart for unknown types.
    """
    chart_type = chart_type.lower().strip()
    builders = {
        "line": line_chart,
        "area": area_chart,
        "bar": bar_chart,
        "comparison": comparison_chart,
        "multi_series": comparison_chart,
    }
    builder = builders.get(chart_type, line_chart)
    return builder(
        df, title=title, y_label=y_label,
        series_columns=series_columns, meta_list=meta_list,
    )
