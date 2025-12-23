"""Plotly chart builders for OHLCV visualization with indicator support."""

from typing import Optional, Union
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Color palette for indicators
INDICATOR_COLORS = {
    "sma_20": "#FFA726",    # Orange
    "sma_50": "#42A5F5",    # Blue
    "ema_12": "#66BB6A",    # Green
    "ema_26": "#EF5350",    # Red
    "bband_lower_20": "#78909C",  # Gray
    "bband_mid_20": "#90A4AE",    # Light gray
    "bband_upper_20": "#78909C",  # Gray
}


def create_candlestick_chart(
    df: pd.DataFrame,
    title: str = "OHLCV Chart",
    show_volume: bool = True,
    overlays: Optional[list[str]] = None,
) -> go.Figure:
    """Create an interactive candlestick chart with volume and overlays.
    
    Args:
        df: DataFrame with OHLCV columns and DatetimeIndex.
        title: Chart title.
        show_volume: Whether to show volume bars.
        overlays: List of column names to overlay on price chart.
        
    Returns:
        Plotly Figure object.
    """
    if show_volume and "volume" in df.columns:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
        )
    else:
        fig = make_subplots(rows=1, cols=1)
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )
    
    # Add overlay indicators
    if overlays:
        for col in overlays:
            if col in df.columns:
                color = INDICATOR_COLORS.get(col, "#FFFFFF")
                
                # Bollinger bands: fill between upper and lower
                if "bband_lower" in col:
                    # Add as dashed line
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[col],
                            mode="lines",
                            name=col.replace("_", " ").title(),
                            line=dict(color=color, width=1, dash="dot"),
                            opacity=0.7,
                        ),
                        row=1, col=1,
                    )
                elif "bband_upper" in col:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[col],
                            mode="lines",
                            name=col.replace("_", " ").title(),
                            line=dict(color=color, width=1, dash="dot"),
                            fill="tonexty",
                            fillcolor="rgba(120, 144, 156, 0.1)",
                            opacity=0.7,
                        ),
                        row=1, col=1,
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[col],
                            mode="lines",
                            name=col.replace("_", " ").title(),
                            line=dict(color=color, width=1.5),
                        ),
                        row=1, col=1,
                    )
    
    # Volume bars
    if show_volume and "volume" in df.columns:
        colors = [
            "#26a69a" if close >= open_ else "#ef5350"
            for close, open_ in zip(df["close"], df["open"])
        ]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.7,
            ),
            row=2, col=1,
        )
        
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2 if show_volume else 1, col=1)
    
    return fig


def create_line_chart(
    df: pd.DataFrame,
    column: str = "close",
    title: str = "Price Chart",
    overlays: Optional[list[str]] = None,
) -> go.Figure:
    """Create a simple line chart with optional overlays.
    
    Args:
        df: DataFrame with the specified column and DatetimeIndex.
        column: Column to plot.
        title: Chart title.
        overlays: List of column names to overlay.
        
    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[column],
            mode="lines",
            name=column.capitalize(),
            line=dict(color="#2196f3", width=2),
        )
    )
    
    # Add overlay indicators
    if overlays:
        for col in overlays:
            if col in df.columns:
                color = INDICATOR_COLORS.get(col, "#FFFFFF")
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[col],
                        mode="lines",
                        name=col.replace("_", " ").title(),
                        line=dict(color=color, width=1.5),
                    )
                )
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=column.capitalize(),
        height=500,
        template="plotly_dark",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    return fig


def create_indicator_chart(
    df: pd.DataFrame,
    columns: Union[str, list[str]],
    title: str = "Indicator",
    yaxis_range: Optional[list[float]] = None,
    histogram: Optional[str] = None,
) -> go.Figure:
    """Create a chart for momentum/oscillator indicators.
    
    Args:
        df: DataFrame with indicator columns.
        columns: Column name(s) to plot.
        title: Chart title.
        yaxis_range: Optional [min, max] for y-axis.
        histogram: Optional column name for histogram bars.
        
    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()
    
    if isinstance(columns, str):
        columns = [columns]
    
    colors = ["#2196f3", "#FFA726", "#66BB6A", "#EF5350"]
    
    # Add histogram first (so lines are on top)
    if histogram and histogram in df.columns:
        hist_colors = [
            "#26a69a" if v >= 0 else "#ef5350"
            for v in df[histogram].fillna(0)
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df[histogram],
                name="Histogram",
                marker_color=hist_colors,
                opacity=0.5,
            )
        )
    
    # Add line traces
    for i, col in enumerate(columns):
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="lines",
                    name=col.replace("_", " ").title(),
                    line=dict(color=colors[i % len(colors)], width=1.5),
                )
            )
    
    # Add reference lines for RSI/Stochastic
    if yaxis_range == [0, 100]:
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5)
    
    # Add zero line for MACD
    if histogram:
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=title,
        height=250,
        template="plotly_dark",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=50, r=50, t=60, b=30),
    )
    
    if yaxis_range:
        fig.update_yaxes(range=yaxis_range)
    
    return fig
