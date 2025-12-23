"""Plotly chart builders for OHLCV visualization."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_candlestick_chart(
    df: pd.DataFrame,
    title: str = "OHLCV Chart",
    show_volume: bool = True,
) -> go.Figure:
    """Create an interactive candlestick chart with volume.
    
    Args:
        df: DataFrame with OHLCV columns and DatetimeIndex.
        title: Chart title.
        show_volume: Whether to show volume bars.
        
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
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2 if show_volume else 1, col=1)
    
    return fig


def create_line_chart(
    df: pd.DataFrame,
    column: str = "close",
    title: str = "Price Chart",
) -> go.Figure:
    """Create a simple line chart.
    
    Args:
        df: DataFrame with the specified column and DatetimeIndex.
        column: Column to plot.
        title: Chart title.
        
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
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=column.capitalize(),
        height=400,
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    return fig
